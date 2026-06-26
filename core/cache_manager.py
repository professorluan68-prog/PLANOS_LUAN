# core/cache_manager.py
import hashlib
import json
import os
import tempfile
import time
from typing import Optional


class CacheCorruptedError(Exception):
    pass


class CacheManager:
    def __init__(self, cache_dir: str = ".cache", schema_version: str = "v1"):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_dir = cache_dir
        self.schema_version = schema_version

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def key_for(self, file_bytes: bytes, params: dict) -> str:
        """
        Gera chave determinística: hash(file_bytes) : hash(params) : schema_version
        """
        params_hash = self._hash(json.dumps(params, sort_keys=True).encode("utf-8"))
        return f"{self._hash(file_bytes)}:{params_hash}:{self.schema_version}"

    def _path(self, key: str) -> str:
        safe = key.replace("/", "_").replace(":", "_")
        return os.path.join(self.cache_dir, safe + ".json")

    def set(self, key: str, value: dict):
        """
        Escrita atômica: grava em arquivo temporário e faz os.replace()
        Armazena metadata mínima para validação futura.
        """
        path = self._path(key)
        tmp = tempfile.NamedTemporaryFile(delete=False, dir=self.cache_dir)
        try:
            payload = {
                "schema_version": self.schema_version,
                "created_at": int(time.time()),
                "value": value,
            }
            tmp.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, path)
        finally:
            if os.path.exists(tmp.name):
                try:
                    os.remove(tmp.name)
                except Exception:
                    pass

    def get(self, key: str) -> Optional[dict]:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                payload = json.load(f)
            if payload.get("schema_version") != self.schema_version:
                # Invalida automaticamente se schema mudou
                return None
            return payload.get("value")
        except Exception:
            # Arquivo corrompido: remover e retornar miss
            try:
                os.remove(path)
            except Exception:
                pass
            return None

    def invalidate_by_prefix(self, prefix: str):
        """
        Invalida arquivos cujo nome comece com prefix.
        Útil para invalidar por prompt_version.
        """
        for fname in os.listdir(self.cache_dir):
            if fname.startswith(prefix):
                try:
                    os.remove(os.path.join(self.cache_dir, fname))
                except Exception:
                    pass
