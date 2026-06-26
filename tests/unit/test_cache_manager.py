# tests/unit/test_cache_manager.py
import os

from core.cache_manager import CacheManager


def test_key_determinism(tmp_path):
    cm = CacheManager(str(tmp_path), schema_version="v1")
    b = b"pdf-bytes"
    params = {"usar_ia": True, "perfil": "A"}
    k1 = cm.key_for(b, params)
    k2 = cm.key_for(b, params)
    assert k1 == k2


def test_set_get_and_schema(tmp_path):
    cm = CacheManager(str(tmp_path), schema_version="v1")
    b = b"pdf-bytes"
    params = {"usar_ia": False}
    k = cm.key_for(b, params)
    cm.set(k, {"plan": "ok"})
    got = cm.get(k)
    assert got is not None and got.get("plan") == "ok"
    cm2 = CacheManager(str(tmp_path), schema_version="v2")
    assert cm2.get(k) is None


def test_atomic_write(tmp_path):
    cm = CacheManager(str(tmp_path), schema_version="v1")
    b = b"pdf-bytes"
    params = {"usar_ia": True}
    k = cm.key_for(b, params)
    cm.set(k, {"plan": "ok"})
    path = cm._path(k)
    assert os.path.exists(path)


def test_corrupted_cache_file_is_removed(tmp_path):
    cm = CacheManager(str(tmp_path), schema_version="v1")
    k = cm.key_for(b"pdf-bytes", {"usar_ia": True})
    path = cm._path(k)
    with open(path, "w", encoding="utf-8") as f:
        f.write("{json-invalido")

    assert cm.get(k) is None
    assert not os.path.exists(path)
