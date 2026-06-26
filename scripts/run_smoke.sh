#!/usr/bin/env bash
set -e
python - <<PY
from core.cache_manager import CacheManager
from core.ia_client import IAClient
print("Smoke: instantiate components")
cm = CacheManager(".cache_test", "v1")
print("Cache OK")
# IAClient smoke (no network call)
ia = IAClient("http://example.invalid", "key", max_retries=0)
print("IAClient OK")
PY
echo "Smoke OK"
