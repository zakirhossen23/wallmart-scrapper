import re
import json
import logging
from curl_cffi import requests as cr

logger = logging.getLogger("walmart_scraper.client")

BROWSE_HASH = "e5013b02d3de9bbb6183548853d3cf6ba40cc236b29ea7a797d1629408dc18d4"
CONTENT_PAGE_HASH = "ac7d09f5c2e4aaed2cd7387144b899e6a30ebb22b8ccbca9fc5fb97a04626916"

class WalmartClient:
    def __init__(self, store_id="3081", impersonate="chrome", timeout=45):
        self.store_id = str(store_id)
        self.impersonate = impersonate
        self.timeout = timeout
        self.cookies = {
            "assortmentStoreId": self.store_id,
            "hasLocData": "1"
        }
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def fetch_page_ssr(self, url):
        """
        Fetches an SSR browse or cp page and extracts __NEXT_DATA__.
        """
        try:
            r = cr.get(url, impersonate=self.impersonate, cookies=self.cookies, headers=self.headers, timeout=self.timeout)
            if r.status_code != 200:
                logger.warning(f"HTTP {r.status_code} for {url}")
                return None
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
            if not m:
                logger.warning(f"No __NEXT_DATA__ in response for {url}")
                return None
            return json.loads(m.group(1))
        except Exception as e:
            logger.error(f"Error fetching SSR {url}: {e}")
            return None

    def fetch_browse_graphql(self, cat_id, page=1, ps=40):
        """
        Calls Walmart's GraphQL Browse endpoint for deep pagination.
        """
        url = f"https://www.walmart.com/orchestra/snb/graphql/Browse/{BROWSE_HASH}/browse"
        variables = {
            "id": "",
            "affinityOverride": "default",
            "pap": "{\"polaris\":{\"ms_max_page_within_rerank\":10,\"ms_slp\":0,\"ms_triggered\":true}}",
            "dealsId": "",
            "query": "",
            "nudgeContext": "",
            "page": page,
            "prg": "mWeb",
            "catId": str(cat_id),
            "facet": "",
            "sort": "best_match",
            "rawFacet": "",
            "seoPath": "",
            "ps": 20,
            "limit": ps,
            "ptss": "",
            "trsp": "",
            "beShelfId": "",
            "recall_set": "",
            "module_search": "",
            "min_price": "",
            "max_price": "",
            "storeSlotBooked": "",
            "additionalQueryParams": {
                "hidden_facet": None,
                "translation": None,
                "isMoreOptionsTileEnabled": True,
                "rootDimension": "",
                "altQuery": "",
                "selectedFilter": "",
                "neuralSearchSeeAll": False,
                "enableGenericItemTileOptions": True,
                "isLMPBrowsePage": False
            },
            "searchArgs": {
                "query": "",
                "cat_id": str(cat_id),
                "prg": "mWeb",
                "facet": ""
            },
            "enableCopyBlock": True,
            "enableVariantCount": False,
            "enableSlaBadgeV2": True,
            "enableUnifiedProductFragment": True,
            "enableESSCarousel": False,
            "fitmentFieldParams": {
                "powerSportEnabled": True,
                "dynamicFitmentEnabled": True,
                "extendedAttributesEnabled": True,
                "extendedAttributesV2Enabled": True,
                "fuelTypeEnabled": True
            },
            "fitmentSearchParams": {
                "id": "",
                "affinityOverride": "default",
                "pap": "{\"polaris\":{\"ms_max_page_within_rerank\":10,\"ms_slp\":0,\"ms_triggered\":true}}",
                "dealsId": "",
                "query": "",
                "nudgeContext": "",
                "page": page,
                "prg": "mWeb",
                "catId": str(cat_id),
                "facet": "",
                "sort": "best_match",
                "rawFacet": "",
                "seoPath": "",
                "ps": 20,
                "limit": ps,
                "ptss": "",
                "trsp": "",
                "beShelfId": "",
                "recall_set": "",
                "module_search": "",
                "min_price": "",
                "max_price": "",
                "storeSlotBooked": "",
                "additionalQueryParams": {
                    "hidden_facet": None,
                    "translation": None,
                    "isMoreOptionsTileEnabled": True,
                    "rootDimension": "",
                    "altQuery": "",
                    "selectedFilter": "",
                    "neuralSearchSeeAll": False,
                    "enableGenericItemTileOptions": True,
                    "isLMPBrowsePage": False
                },
                "searchArgs": {
                    "query": "",
                    "cat_id": str(cat_id),
                    "prg": "mWeb",
                    "facet": ""
                },
                "enableCopyBlock": True,
                "enableVariantCount": False,
                "enableSlaBadgeV2": True,
                "enableUnifiedProductFragment": True,
                "enableESSCarousel": False,
                "cat_id": str(cat_id),
                "_be_shelf_id": ""
            },
            "searchParams": {
                "id": "",
                "affinityOverride": "default",
                "pap": "{\"polaris\":{\"ms_max_page_within_rerank\":10,\"ms_slp\":0,\"ms_triggered\":true}}",
                "dealsId": "",
                "query": "",
                "nudgeContext": "",
                "page": page,
                "prg": "mWeb",
                "catId": str(cat_id),
                "facet": "",
                "sort": "best_match",
                "rawFacet": "",
                "seoPath": "",
                "ps": 20,
                "limit": ps,
                "ptss": "",
                "trsp": "",
                "beShelfId": "",
                "recall_set": "",
                "module_search": "",
                "min_price": "",
                "max_price": "",
                "storeSlotBooked": "",
                "additionalQueryParams": {
                    "hidden_facet": None,
                    "translation": None,
                    "isMoreOptionsTileEnabled": True,
                    "rootDimension": "",
                    "altQuery": "",
                    "selectedFilter": "",
                    "neuralSearchSeeAll": False,
                    "enableGenericItemTileOptions": True,
                    "isLMPBrowsePage": False
                },
                "searchArgs": {
                    "query": "",
                    "cat_id": str(cat_id),
                    "prg": "mWeb",
                    "facet": ""
                },
                "enableCopyBlock": True,
                "enableVariantCount": False,
                "enableSlaBadgeV2": True,
                "enableUnifiedProductFragment": True,
                "enableESSCarousel": False,
                "cat_id": str(cat_id),
                "_be_shelf_id": ""
            },
            "enableFashionTopNav": False,
            "fetchMarquee": True,
            "fetchSkyline": True,
            "fetchSbaTop": True,
            "fetchDataV1": True,
            "fetchDataV2": True,
            "fungibilityEnabled": False,
            "fetchGallery": False,
            "fetchDac": True,
            "enablePortableFacets": True,
            "tenant": "WM_GLASS",
            "pageType": "BrowsePage",
            "enableFacetCount": True,
            "enableMultiSave": False,
            "enableInStoreShelfMessage": False,
            "fSeo": True,
            "enableSellerType": False,
            "enableItemRank": False,
            "enableOptimisticWeightUpdate": False,
            "enableFulfillmentTagsEnhacements": False,
            "enableRxDrugScheduleModal": False,
            "enablePromoData": True,
            "enableAdsPromoData": False,
            "enableSeoLangUrl": False,
            "enableImageBannerCarousel": False,
            "enableHero4": False,
            "enableSeoBrowseMetaDataShortDesc": False,
            "enableCanAddToList": False,
            "enablePromotionMessages": False,
            "enableDebugAnalyticsTags": False,
            "enableSignInToSeePrice": False,
            "enableSimpleEmailSignUp": False,
            "enableModuleReposition": False,
            "enableFilterGrouping": False,
            "enableUnifiedSchema": True,
            "version": "v2",
            "postProcessingVersion": 2,
            "enableAdsUnifiedProductTile": False
        }
        headers = {
            "accept": "application/json",
            "accept-language": "en-US",
            "wm_mp": "true",
            "x-apollo-operation-name": "Browse",
            "x-enable-server-timing": "1",
            "x-latency-trace": "1",
            "x-o-bu": "WALMART-US",
            "x-o-ccm": "server",
            "x-o-correlation-id": "AqM8ZEy1WFevXNJboSX1aJMpQw2kpj9SiSlz",
            "x-o-gql-query": "query Browse",
            "x-o-mart": "B2C",
            "x-o-platform": "rweb",
            "x-o-platform-version": "usweb-1.320.0-517fba2570874f63de2e7ff772f42aecfa8cd91d-0150924r",
            "x-o-segment": "oaoh"
        }
        try:
            r = cr.get(url, params={"variables": json.dumps(variables)}, impersonate=self.impersonate,
                       headers=headers, cookies=self.cookies, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
            else:
                logger.warning(f"Browse GraphQL status {r.status_code}: {r.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Error calling Browse GraphQL: {e}")
            return None
