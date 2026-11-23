from time import monotonic, sleep, time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from limits import parse
from niagads.api.common.config import Settings

RATE_LIMITED_URL = "/record/gene/APOE"
EXEMPT_URL = "/service/feature?id=APOE&flank=25"


@pytest.mark.parametrize("client", [(f"rate-limit-{uuid4()}", 50000)], indirect=True)
def test_requests_respecting_configured_window_succeed(client: TestClient) -> None:
    limit = parse(Settings.from_env().API_RATE_LIMIT)
    started = time()

    for number in range(1, limit.amount + 1):
        response = client.get(RATE_LIMITED_URL)
        assert (
            response.status_code == 200
        ), f"Request {number}/{limit.amount} returned {response.status_code}."
        assert int(response.headers["X-RateLimit-Limit"]) == limit.amount
        assert int(response.headers["X-RateLimit-Remaining"]) == limit.amount - number

    reset = float(response.headers["X-RateLimit-Reset"])
    assert started + limit.get_expiry() <= reset <= started + limit.get_expiry() + 2
    assert time() < reset, "Requests took longer than the configured window."

    sleep(max(0, reset - time()) + 1)
    response = client.get(RATE_LIMITED_URL)
    assert (
        response.status_code == 200
    ), f"Request after the configured window returned {response.status_code}."
    assert int(response.headers["X-RateLimit-Remaining"]) == limit.amount - 1


@pytest.mark.parametrize("client", [(f"rate-limit-{uuid4()}", 50000)], indirect=True)
def test_requests_exceeding_configured_allowance_are_rejected(
    client: TestClient,
) -> None:
    limit = parse(Settings.from_env().API_RATE_LIMIT)
    started = monotonic()

    for number in range(1, limit.amount + 1):
        response = client.get(RATE_LIMITED_URL)
        assert (
            response.status_code == 200
        ), f"Request {number}/{limit.amount} returned {response.status_code}."
        assert int(response.headers["X-RateLimit-Limit"]) == limit.amount
        assert int(response.headers["X-RateLimit-Remaining"]) == limit.amount - number

    response = client.get(RATE_LIMITED_URL)
    assert (
        monotonic() - started < limit.get_expiry()
    ), "Requests took longer than the configured window."
    assert response.status_code == 429, (
        f"Request {limit.amount + 1} exceeded the configured allowance "
        f"but returned {response.status_code}."
    )
    assert int(response.headers["X-RateLimit-Remaining"]) == 0
    assert 0 < int(response.headers["Retry-After"]) <= limit.get_expiry()


@pytest.mark.parametrize("client", [(f"rate-limit-{uuid4()}", 50000)], indirect=True)
def test_exempt_route_returns_200_without_rate_limit_headers(
    client: TestClient,
) -> None:
    response = client.get(EXEMPT_URL)
    assert (
        response.status_code == 200
    ), f"Expected HTTP 200 from the exempt route, got {response.status_code}."
    headers = [
        name
        for name in response.headers
        if name.startswith("x-ratelimit-") or name == "retry-after"
    ]
    assert not headers, f"Exempt route returned rate-limit headers {headers}."
