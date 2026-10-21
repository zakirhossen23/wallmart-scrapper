import re
import logging

logger = logging.getLogger("walmart_scraper.navigator")

class CategoryNavigator:
    def __init__(self, client):
        self.client = client

    def discover_subcategories(self, category_name, url, notes=""):
        notes_lower = (notes or "").lower()
        exclude_recipes = "recipe" in notes_lower
        exclude_shop_all = "shop all" in notes_lower
        exclude_farm_animals = "farm animals" in notes_lower

        subcategories = []
        seen_ids = set()

        nd = self.client.fetch_page_ssr(url)
        if not nd:
            logger.error(f"Could not fetch landing page for category {category_name} at {url}")
            root_id = self._extract_cat_id(url)
            if root_id:
                subcategories.append({"name": category_name, "cat_id": root_id, "url": url})
            return subcategories

        pp = nd.get("props", {}).get("pageProps", {})
        init_data = pp.get("initialTempoData") or pp.get("initialData") or {}
        cl = init_data.get("contentLayout") or {}
        modules = cl.get("modules") or []

        for m in modules:
            mtype = m.get("type")
            cfg = m.get("configs") or {}
            if mtype == "SeoLinkModule":
                for cat in (cfg.get("categoriesData") or []):
                    cname = cat.get("name") or ""
                    for sub in (cat.get("subcategories") or []):
                        slink = sub.get("subCategoryLink") or {}
                        stitle = slink.get("title") or slink.get("linkText") or ""
                        sval = (slink.get("clickThrough") or {}).get("value") or ""
                        
                        full_name = f"{cname} - {stitle}".strip(" -")
                        if self._should_exclude(full_name, exclude_recipes, exclude_shop_all, exclude_farm_animals):
                            continue
                            
                        cat_id = self._extract_cat_id(sval)
                        if cat_id and cat_id not in seen_ids:
                            seen_ids.add(cat_id)
                            subcategories.append({
                                "name": full_name,
                                "cat_id": cat_id,
                                "url": f"https://www.walmart.com{sval}" if sval.startswith("/") else sval
                            })

            elif mtype == "HubSpokesNxM":
                for r_key in ["rows4", "rows6"]:
                    for r in (cfg.get(r_key) or []):
                        for cat in (r.get("categories") or []):
                            cname = cat.get("name") or ""
                            if self._should_exclude(cname, exclude_recipes, exclude_shop_all, exclude_farm_animals):
                                continue
                            cval = (cat.get("image", {}).get("clickThrough") or {}).get("value") or ""
                            cat_id = self._extract_cat_id(cval)
                            if cat_id and cat_id not in seen_ids:
                                seen_ids.add(cat_id)
                                subcategories.append({
                                    "name": cname,
                                    "cat_id": cat_id,
                                    "url": f"https://www.walmart.com{cval}" if cval.startswith("/") else cval
                                })

            elif mtype == "SearchSortFilterModule":
                for f in (cfg.get("allSortAndFilterFacets") or []):
                    if f.get("type") == "cat_id":
                        for val in (f.get("values") or []):
                            vtitle = val.get("title") or val.get("name") or ""
                            if self._should_exclude(vtitle, exclude_recipes, exclude_shop_all, exclude_farm_animals):
                                continue
                            vid = val.get("id")
                            vurl = val.get("baseSeoURL") or ""
                            if vid and vid not in seen_ids:
                                seen_ids.add(vid)
                                subcategories.append({
                                    "name": vtitle,
                                    "cat_id": vid,
                                    "url": f"https://www.walmart.com{vurl}" if vurl.startswith("/") else vurl
                                })

        if not subcategories:
            root_cat_id = self._extract_cat_id(url)
            if root_cat_id:
                subcategories.append({
                    "name": category_name,
                    "cat_id": root_cat_id,
                    "url": url
                })

        logger.info(f"Discovered {len(subcategories)} subcategories for {category_name}")
        return subcategories

    def _should_exclude(self, title, exclude_recipes, exclude_shop_all, exclude_farm_animals):
        t = title.lower()
        if exclude_recipes and ("recipe" in t or "recipe-library" in t):
            return True
        if exclude_shop_all and ("shop all" in t):
            return True
        if exclude_farm_animals and ("farm animal" in t):
            return True
        return False

    def _extract_cat_id(self, url):
        m = re.search(r'cat_id=([0-9_]+)', url)
        if m:
            return m.group(1)
        m = re.search(r'/([0-9]{4,}(?:_[0-9]+)*)(?:\?|$)', url)
        if m:
            return m.group(1)
        return ""
