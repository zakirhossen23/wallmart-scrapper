# Contest Submission Package: Production-Ready Walmart Scraper for Microsoft Azure

## 1. Overview & Architecture
This solution provides a direct HTTP, browser-fingerprinted scraper engine designed specifically for deployment on Microsoft Azure without continuous manual intervention.

### Core Architecture Components:
- **Direct HTTP Engine (`walmart_scraper/client.py`):** Uses TLS/HTTP2 browser fingerprinting (via `curl_cffi` impersonating modern Chrome) to query Walmart's native GraphQL service (`Browse` and `ContentPage`) directly, avoiding the heavy memory and compute overhead of headless browser automation.
- **Dynamic Taxonomy Navigator (`walmart_scraper/navigator.py`):** Discovers all nested subcategory nodes from Walmart's category landing hubs while strictly obeying exclusion rules (e.g. omitting `'Shop All Foods'`, `'Recipes'`, and `'Farm Animals'` per `config/categories.csv`).
- **Data Parser & Normalizer (`walmart_scraper/parser.py`):** Enforces the exact 22-field JSON schema in required order, parses display prices, extracts displayed PPM (`$0.25/oz`, `3.2 ¢/fl oz`), separates volume deals from digital coupons, and excludes approximate weight products.
- **Fail-Safe Pipeline & Azure Deployment (`walmart_scraper/pipeline.py`):** Guarantees zero-data-loss checkpointing, validates yield against minimum thresholds, and ensures a failed or blocked run never overwrites existing good data (`latest_good.json`).

---

## 2. Location & Fulfillment Verification
- **Store Pinning:** Every request transmits the configured Walmart store ID (e.g., store `3081` in Sacramento, CA) via `assortmentStoreId=3081` and `stores=3081`.
- **Fulfillment Filtering:** Distinguishes local store inventory from shipping-only and 3P marketplace items by verifying `sellerName == "Walmart.com"`, `fulfillmentType == "STORE"`, and local pickup eligibility in `fulfillmentSummary`.
- **Location Verification:** Confirms store identity against `pageMetadata.location` (verifying postal code `95829`, city `Sacramento`, state `CA`).

---

## 3. Data Schema Compliance (Exact 22-Field Order)
Each record strictly outputs:
1. `zipcode`
2. `store_name`
3. `store_location`
4. `store_logo`
5. `store_brand` (`"yes"` for identified private labels, otherwise `"no"`)
6. `category`
7. `sub_category`
8. `product_title`
9. `weight` (excludes approximate weight records containing `"approx"` / `"approximately"`)
10. `regular_price`
11. `sale_price`
12. `volume_deals_description`
13. `volume_deals_price`
14. `digital_deals_description`
15. `digital_deals_price`
16. `image_url`
17. `url`
18. `upc`
19. `gupc` (strictly `""`)
20. `ppm` (scraped exact as displayed)
21. `unit_price` (strictly `""` for downstream pipeline calculation)
22. `crawl_date` (required as final field)

Missing values are uniformly returned as `""` (empty strings), never `null`.

---

## 4. Microsoft Azure Operating Costs
Because the scraper runs on direct HTTP rather than heavyweight headless Chromium instances:
- **Compute (Azure Container Apps / B1ms Linux VM):** ~1 core, 1 GB RAM needed. Running twice per week for ~2 hours per run totals under **$4.00 – $8.00 / month**.
- **Azure Blob Storage:** Negligible (< **$0.50 / month**) for JSON exports, state checkpoints, and rolling logs.
- **Proxy / IP Rotation:** Residential proxy bandwidth for twice-weekly runs averages ~2-5 GB / month (**~$15.00 – $25.00 / month**).
- **Total Monthly Operating Cost:** **~$20 – $35 / month**.
