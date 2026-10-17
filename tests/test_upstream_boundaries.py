"""Synthetic malformed and slow upstreams; no provider calls or private images."""
import asyncio
import json

import httpx
import pytest

from server.barcodes import _bounded_json
from server.cloud_vision import CloudVisionReader, CloudVisionUnavailable
from server.provider import (
    ProviderFailure, VisionProvider, verify_openrouter_key_limit,
    verify_openrouter_zdr_model, verify_openrouter_beta_spend_cap,
)


@pytest.mark.parametrize("payload", [
    {"choices": [None]},
    {"choices": [[]]},
    {"choices": ["untrusted upstream text"]},
    {"choices": [{"message": None}]},
    {"choices": [{"message": []}]},
    {"choices": [{"message": "untrusted upstream text"}]},
])
def test_malformed_chat_envelopes_are_sanitized(payload, before):
    provider = VisionProvider(
        "https://vision.example/v1", "synthetic-model",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    )
    with pytest.raises(ProviderFailure) as error:
        asyncio.run(provider.analyze(before))
    assert "untrusted upstream text" not in str(error.value)


class SlowResponse(httpx.AsyncByteStream):
    """Keep sending chunks before an inactivity timeout would fire."""
    def __init__(self, payload):
        self.payload = payload
        self.closed = False

    async def __aiter__(self):
        for _ in range(8):
            await asyncio.sleep(0.01)
            yield b" "
        yield json.dumps(self.payload).encode()

    async def aclose(self):
        self.closed = True


@pytest.mark.parametrize("status", [200, 503])
def test_ocr_entire_response_has_a_deadline(status, before):
    stream = SlowResponse({"responses": [{}, {}]})
    reader = CloudVisionReader(
        "synthetic-only-key-for-testing", "synthetic-project",
        timeout=0.025,
        transport=httpx.MockTransport(lambda request: httpx.Response(status, stream=stream)),
    )
    with pytest.raises(CloudVisionUnavailable) as error:
        asyncio.run(reader.read(before, before))
    assert error.value.code == "NETWORK_TIMEOUT"
    assert stream.closed


def test_catalog_entire_response_has_a_deadline():
    stream = SlowResponse({"status": 1})

    async def run():
        async with httpx.AsyncClient(
            timeout=0.025,
            transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)),
        ) as client:
            return await _bounded_json(client, "https://catalog.example/product", {}, 1000)

    assert asyncio.run(run()) is None
    assert stream.closed


METADATA_READERS = [
    (lambda transport: verify_openrouter_key_limit("synthetic-key", transport=transport), 20_000,
     {"data": {"limit": 0.50, "limit_remaining": 0.40, "limit_reset": None,
               "is_management_key": False, "include_byok_in_limit": True}}),
    (lambda transport: verify_openrouter_zdr_model("synthetic-key", "test/model", transport=transport), 12_000_000,
     {"data": [{"model_id": "test/model", "status": 0,
                "supported_parameters": ["response_format", "temperature", "max_tokens"]}]}),
    (lambda transport: verify_openrouter_beta_spend_cap("synthetic-key", transport=transport), 20_000,
     {"data": {"limit": 10.0, "limit_remaining": 5.0, "limit_reset": None,
               "is_management_key": False, "include_byok_in_limit": True}}),
]


@pytest.mark.parametrize("read_metadata,limit,payload", [METADATA_READERS[0], METADATA_READERS[2]],
                         ids=["evaluation_cap", "beta_cap"])
@pytest.mark.parametrize("field", ["limit", "limit_remaining"])
def test_metadata_large_integer_amounts_fail_closed(read_metadata, limit, payload, field):
    malformed = {"data": {**payload["data"], field: 10**400}}
    requests = []

    def respond(request):
        requests.append((request.method, str(request.url)))
        return httpx.Response(200, json=malformed)

    with pytest.raises(ProviderFailure) as error:
        asyncio.run(read_metadata(httpx.MockTransport(respond)))
    expected = ("SPEND_CAP_INVALID" if payload["data"]["limit"] == 10.0 else
                "A non-resetting provider-side spending cap is required before testing.")
    assert str(error.value) == expected
    assert requests == [("GET", "https://openrouter.ai/api/v1/key")]


@pytest.mark.parametrize("read_metadata,limit,payload", METADATA_READERS)
def test_metadata_rejects_oversize_before_reading_remainder(read_metadata, limit, payload):
    class OversizedResponse(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            yield b" " * (limit + 1)
            raise AssertionError("A bounded reader must stop before reading more upstream bytes")

        async def aclose(self):
            self.closed = True

    stream = OversizedResponse()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))
    with pytest.raises(ProviderFailure):
        asyncio.run(read_metadata(transport))
    assert stream.closed


@pytest.mark.parametrize("read_metadata,limit,payload", METADATA_READERS)
def test_metadata_entire_response_has_a_deadline(read_metadata, limit, payload, monkeypatch):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        "server.provider.httpx.AsyncClient",
        lambda **kwargs: original_client(**{**kwargs, "timeout": 0.025}),
    )
    stream = SlowResponse(payload)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))
    with pytest.raises(ProviderFailure):
        asyncio.run(read_metadata(transport))
    assert stream.closed
