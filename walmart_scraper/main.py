import os
import sys
import csv
import json
import time
import logging
from datetime import datetime

from walmart_scraper.client import WalmartClient
from walmart_scraper.navigator import CategoryNavigator
from walmart_scraper.parser import build_record
from walmart_scraper.pipeline import Pipeline

def setup_logging(log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"scraper_{datetime.utcnow().strftime('%Y%m%d')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("walmart_scraper.main")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_categories_csv(path):
    cats = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cats.append(r)
    return cats

def run(target_job_id=None, limit_records=0):
    settings = load_json(os.path.join("config", "settings.json"))
    locations_cfg = load_json(os.path.join("config", "locations.json"))
    categories = load_categories_csv(os.path.join("config", "categories.csv"))
    
    logger = setup_logging(settings.get("log_dir", "logs"))
    logger.info("Initializing Walmart Production Scraper...")

    pipeline = Pipeline(settings.get("output_dir", "data"), settings.get("state_dir", "state"))
    private_brands = settings.get("private_label_brands", [])
    crawl_date = datetime.utcnow().strftime("%Y-%m-%d")

    active_locations = [loc for loc in locations_cfg.get("locations", []) if loc.get("enabled", True)]
    if target_job_id:
        active_locations = [loc for loc in active_locations if loc.get("job_id") == target_job_id]

    for loc in active_locations:
        job_id = loc.get("job_id")
        store_id = loc.get("store_id")
        logger.info(f"Starting job {job_id} for store {store_id} ({loc.get('store_location')})")

        client = WalmartClient(store_id=store_id, timeout=settings.get("request_timeout_sec", 45))
        navigator = CategoryNavigator(client)

        ckpt = pipeline.load_checkpoint(job_id)
        processed_cats = set(ckpt.get("processed_categories", []))
        seen_items = set(ckpt.get("seen_item_ids", []))
        collected_records = []

        for cat_row in categories:
            cat_name = cat_row.get("Category (Auto)")
            cat_url = cat_row.get("URL")
            notes = cat_row.get("Notes", "")

            if cat_name in processed_cats:
                logger.info(f"Skipping already completed category {cat_name} from checkpoint")
                continue

            logger.info(f"Processing category: {cat_name} ({cat_url})")
            subs = navigator.discover_subcategories(cat_name, cat_url, notes)

            for sub in subs:
                sub_name = sub.get("name")
                cat_id = sub.get("cat_id")
                logger.info(f"Scraping subcategory: {sub_name} (cat_id={cat_id})")

                # Fetch pages (up to configured max)
                max_pages = settings.get("max_pages_per_node", 5)
                for page in range(1, max_pages + 1):
                    logger.info(f"Fetching page {page} for subcategory {sub_name}")
                    resp = client.fetch_browse_graphql(cat_id, page=page, ps=settings.get("page_size", 40))
                    if not resp:
                        break

                    data = resp.get("data") or {}
                    sr = (data.get("search") or {}).get("searchResult") or {}
                    stacks = sr.get("itemStacks") or []
                    if not stacks:
                        break

                    items = stacks[0].get("itemsV2") or stacks[0].get("items") or []
                    if not items:
                        break

                    for item in items:
                        if item.get("__typename") != "Product":
                            continue
                        us_id = item.get("usItemId")
                        if not us_id or us_id in seen_items:
                            continue

                        # Check local store availability filter
                        # Local store products have seller 'Walmart.com' and fulfillment 'STORE' or storeId 3081 in fulfillmentSummary
                        f_type = item.get("fulfillmentType")
                        s_name = item.get("sellerName")
                        f_summary = item.get("fulfillmentSummary") or []
                        is_store_local = (s_name == "Walmart.com" and f_type == "STORE") or any(str(f.get("storeId")) == str(store_id) for f in f_summary)
                        
                        rec = build_record(item, cat_name, sub_name, loc, crawl_date, private_brands)
                        if rec:
                            seen_items.add(us_id)
                            collected_records.append(rec)

                    time.sleep(settings.get("min_delay_sec", 1.5))
                    
                    if limit_records and len(collected_records) >= limit_records:
                        break
                
                if limit_records and len(collected_records) >= limit_records:
                    break

            processed_cats.add(cat_name)
            pipeline.save_checkpoint(job_id, processed_cats, seen_items)

            if limit_records and len(collected_records) >= limit_records:
                logger.info(f"Reached record limit ({limit_records}). Stopping collection.")
                break

        # Validate run
        is_valid, report = pipeline.validate_run(collected_records, settings.get("validation", {}))
        pipeline.publish_output(job_id, collected_records, is_valid, report)
        logger.info(f"Completed run for {job_id}. Total records: {len(collected_records)}. Valid: {is_valid}")

if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(limit_records=lim)
