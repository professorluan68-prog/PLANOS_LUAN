# tests/unit/test_ia_client.py
from unittest.mock import patch

import pytest
import requests

from core.ia_client import CircuitOpenError, IAClient


class DummyResp:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        raise requests.HTTPError()


@patch("core.ia_client.requests.post")
@patch("core.ia_client.time.sleep", return_value=None)
def test_no_retry_on_400(_mock_sleep, mock_post):
    mock_post.return_value = DummyResp(400)
    client = IAClient("http://example", "key", max_retries=2)
    with pytest.raises(requests.HTTPError):
        client.generate({"prompt": "x"})


@patch("core.ia_client.requests.post")
@patch("core.ia_client.time.sleep", return_value=None)
def test_retries_on_500_then_success(_mock_sleep, mock_post):
    mock_post.side_effect = [DummyResp(500), DummyResp(200, {"ok": True})]
    client = IAClient("http://example", "key", max_retries=3)
    res = client.generate({"prompt": "x"})
    assert res.get("ok") is True


@patch("core.ia_client.requests.post")
@patch("core.ia_client.time.sleep", return_value=None)
def test_retryable_http_opens_failure_counter(_mock_sleep, mock_post):
    mock_post.return_value = DummyResp(503)
    client = IAClient(
        "http://example", "key", max_retries=1, max_failures=2, cooldown=1
    )
    with pytest.raises(RuntimeError):
        client.generate({"prompt": "x"})
    assert client._failures == 2


def test_circuit_opens_after_failures():
    client = IAClient("http://example", "key", max_failures=2, cooldown=1)
    client._record_failure()
    client._record_failure()
    with pytest.raises(CircuitOpenError):
        client.generate({"prompt": "x"})
