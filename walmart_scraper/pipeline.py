import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("walmart_scraper.pipeline")

class Pipeline:
    def __init__(self, output_dir="data", state_dir="state"):
        self.output_dir = output_dir
        self.state_dir = state_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.state_dir, exist_ok=True)

    def load_checkpoint(self, job_id):
        ckpt_path = os.path.join(self.state_dir, f"{job_id}_checkpoint.json")
        if os.path.exists(ckpt_path):
            try:
                with open(ckpt_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return {"processed_categories": [], "seen_item_ids": []}

    def save_checkpoint(self, job_id, processed_categories, seen_item_ids):
        ckpt_path = os.path.join(self.state_dir, f"{job_id}_checkpoint.json")
        try:
            with open(ckpt_path, "w", encoding="utf-8") as f:
                json.dump({
                    "job_id": job_id,
                    "processed_categories": list(processed_categories),
                    "seen_item_ids": list(seen_item_ids),
                    "updated_at": datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def validate_run(self, records, config_validation):
        """
        Validates minimum count, field completeness, etc.
        Returns (is_valid, validation_report)
        """
        min_total = config_validation.get("min_total_records", 500)
        total_records = len(records)
        
        report = {
            "total_records": total_records,
            "min_required": min_total,
            "passed": True,
            "reasons": []
        }
        
        if total_records < min_total:
            report["passed"] = False
            report["reasons"].append(f"Record count {total_records} below minimum required {min_total}")

        # Check critical fields completeness
        critical_fields = ["zipcode", "store_name", "product_title", "url", "crawl_date"]
        missing_counts = {f: 0 for f in critical_fields}
        for r in records:
            for f in critical_fields:
                if not r.get(f):
                    missing_counts[f] += 1
                    
        for f, count in missing_counts.items():
            if count > 0:
                report["passed"] = False
                report["reasons"].append(f"Field {f} missing in {count} records")

        return report["passed"], report

    def publish_output(self, job_id, records, is_valid, validation_report):
        """
        Saves output safely. Never overwrites the last successful run if validation fails.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_file = os.path.join(self.output_dir, f"{job_id}_{timestamp}.json")
        last_good_file = os.path.join(self.output_dir, f"{job_id}_latest_good.json")
        report_file = os.path.join(self.output_dir, f"{job_id}_{timestamp}_report.json")

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(validation_report, f, indent=2)

        if is_valid:
            with open(last_good_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            logger.info(f"Published latest good export with {len(records)} records to {last_good_file}")
        else:
            logger.warning(f"Run validation FAILED. Preserving existing latest_good output. Run archived at {run_file}")
