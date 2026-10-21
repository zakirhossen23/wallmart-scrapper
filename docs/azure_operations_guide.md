# Walmart Production Scraper - Operation & Azure Deployment Guide

## 1. Architecture Overview
This scraper uses direct, browser-fingerprinted HTTP (via `curl_cffi` impersonating modern Chrome) to query Walmart's native GraphQL service (`Browse` and `ContentPage`) directly without browser automation overhead:
- **Zero-Headless Footprint:** Runs fast, lightweight, and low-cost on Microsoft Azure (Linux VMs, Azure Container Apps, or Azure Functions).
- **Location Pinning:** Attaches `assortmentStoreId` and `stores` context to lock inventory to the specified Walmart Supercenter.
- **Fulfillment Distinction:** Distinguishes and prioritizes local store offers over 3P Marketplace and shipping-only items.
- **Subcategory Discovery:** Automatically discovers nested subcategories from category hubs while respecting explicit exclusion lists (such as `Shop All Foods` and `Recipes`).

---

## 2. Configuration & Extending Locations

### Adding a New Walmart Store
Open `config/locations.json` and add a new store entry:
```json
{
  "job_id": "dallas-2451",
  "store_id": "2451",
  "zipcode": "75201",
  "store_name": "Walmart Supercenter",
  "store_location": "Dallas, TX",
  "store_logo": "https://i5.walmartimages.com/dfw/63fd9f59-14e2/9d304ce6-96de-4331-b8ec-c5191236bf6a/v1/walmartLogo.svg",
  "enabled": true
}
```
No code modification is required.

### Adding New Categories
Edit `config/categories.csv` to add new retailer category URLs and exclusions.

---

## 3. Microsoft Azure Deployment

### Option A: Azure Container Apps / Scheduled Cron
1. Deploy storage using ARM template: `azure/azure_deploy.json`.
2. Schedule a cron job:
   ```cron
   0 2 * * 2,5
   ```
   (Runs twice weekly, e.g., Tuesday and Friday mornings at 02:00 UTC).

### Option B: Azure DevOps / GitHub Actions
Use the pre-configured workflow in `azure/azure_pipeline.yml`.

---

## 4. Checkpoints & Safe Recovery
- Progress is continuously saved to `state/{job_id}_checkpoint.json`.
- If a run is interrupted or encounters network disconnects, rerunning the command automatically skips already completed categories and resumes collection safely.
- Failed or incomplete runs never overwrite the verified export (`{job_id}_latest_good.json`).
