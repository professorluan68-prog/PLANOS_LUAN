# core/ia_client.py
import random
import threading
import time
from typing import Any, Dict

import requests


class CircuitOpenError(RuntimeError):
    pass


class IAClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 20,
        max_retries: int = 4,
        max_failures: int = 6,
        cooldown: int = 60,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._failures = 0
        self._max_failures = max_failures
        self._cooldown = cooldown
        self._lock = threading.Lock()
        self._circuit_open_until = 0

    def _is_circuit_open(self) -> bool:
        return time.time() < self._circuit_open_until

    def _record_failure(self):
        with self._lock:
            self._failures += 1
            if self._failures >= self._max_failures:
                self._circuit_open_until = time.time() + self._cooldown

    def _record_success(self):
        with self._lock:
            self._failures = 0
            self._circuit_open_until = 0

    def _request(self, payload: Dict[str, Any]):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = requests.post(
            self.base_url, json=payload, headers=headers, timeout=self.timeout
        )
        return resp

    def _backoff_seconds(self, attempt: int) -> float:
        return (2**attempt) + random.uniform(0, 1)

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz chamadas com retries/backoff/jitter e abre circuito em falhas repetidas.
        Em caso de falha irreversivel, lanca excecao.
        """
        if self._is_circuit_open():
            raise CircuitOpenError("IA circuit is open; skipping call")

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._request(payload)
                status = resp.status_code
                if 200 <= status < 300:
                    self._record_success()
                    return resp.json()
                if 400 <= status < 500 and status != 429:
                    raise requests.HTTPError(
                        f"Permanent client error: {status}", response=resp
                    )
                raise requests.HTTPError(
                    f"Retryable upstream error: {status}", response=resp
                )
            except requests.RequestException as e:
                last_error = e
                if isinstance(e, requests.HTTPError) and e.response is not None:
                    status = e.response.status_code
                    if 400 <= status < 500 and status != 429:
                        raise
                self._record_failure()
                if attempt >= self.max_retries:
                    break
                time.sleep(self._backoff_seconds(attempt + 1))

        raise RuntimeError("Max retries reached for IA call") from last_error
