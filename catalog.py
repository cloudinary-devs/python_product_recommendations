# Data pipeline that loads the product catalog and its AI-generated tags from
# Cloudinary, normalizes it, and caches it for the recommendation model.

import json
import logging
import os
import threading
import time

import certifi
import cloudinary
import cloudinary.api
import urllib3

log = logging.getLogger(__name__)

# Every product image is uploaded with this tag so it can be listed later.
PRODUCT_TAG = "my_products"

# Cloud used for the public gallery when no Cloudinary credentials are set.
FALLBACK_CLOUD_NAME = "demo"

CACHE_TTL = int(os.environ.get("CATALOG_CACHE_TTL", "300"))

_http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
_lock = threading.Lock()
_cache = {"expires": 0.0, "catalog": None}


def cloud_name():
    return cloudinary.config().cloud_name or FALLBACK_CLOUD_NAME


def has_api_credentials():
    config = cloudinary.config()
    return bool(config.cloud_name and config.api_key and config.api_secret)


def _normalize(resource):
    return {
        "public_id": resource["public_id"],
        "version": resource.get("version"),
        "width": resource.get("width"),
        "height": resource.get("height"),
        "tags": resource.get("tags") or [],
    }


def _fetch_with_admin_api():
    # One paginated Admin API call returns every product with its tags,
    # instead of one rate-limited resource() call per asset.
    resources, cursor = [], None
    while True:
        options = {"tags": True, "max_results": 500}
        if cursor:
            options["next_cursor"] = cursor
        response = cloudinary.api.resources_by_tag(PRODUCT_TAG, **options)
        resources.extend(response.get("resources", []))
        cursor = response.get("next_cursor")
        if not cursor:
            return resources


def _fetch_public_list():
    # The client-side resource list needs no credentials but doesn't include
    # tags, so it can populate the gallery but can't drive recommendations.
    url = f"https://res.cloudinary.com/{cloud_name()}/image/list/{PRODUCT_TAG}.json"
    response = _http.request("GET", url, timeout=10.0)
    if response.status != 200:
        raise RuntimeError(f"Resource list request failed ({response.status}): {url}")
    return json.loads(response.data).get("resources", [])


def fetch_catalog():
    """Fetch and normalize all product assets, bypassing the cache."""
    if has_api_credentials():
        resources = _fetch_with_admin_api()
    else:
        log.warning("No Cloudinary API credentials; loading the public list without tags.")
        resources = _fetch_public_list()
    return [_normalize(r) for r in resources]


def get_catalog(force_refresh=False):
    """Return the cached catalog, refreshing it when the TTL has expired."""
    with _lock:
        if force_refresh or _cache["catalog"] is None or time.time() >= _cache["expires"]:
            _cache["catalog"] = fetch_catalog()
            _cache["expires"] = time.time() + CACHE_TTL
        return _cache["catalog"]


def clear_cache():
    with _lock:
        _cache["catalog"] = None
        _cache["expires"] = 0.0
