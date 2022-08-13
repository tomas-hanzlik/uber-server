import httpx
import pytest
import respx
from freezegun import freeze_time
from httpx import Response
from starlette import status

from app.config import settings

FREEZE_TIME_ISO_STR = "2022-08-11T10:18:23+00:00"


@pytest.mark.parametrize("headers", [{"Authorization": f"Bearer a"}, {}])
def test_current_iso_dt_unauthorized(headers, v1_test_client):
    resp = v1_test_client.get("v1/now", headers=headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("headers", [{"Authorization": f"Bearer a"}, {}])
def test_track_location_unauthorized(headers, v1_test_client):
    resp = v1_test_client.get("v1/VIP/1", headers=headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@freeze_time(FREEZE_TIME_ISO_STR)
def test_current_iso_dt(v1_test_client):
    resp = v1_test_client.get(
        "v1/now", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"now": FREEZE_TIME_ISO_STR}


def test_track_location_point_in_time_invalid(v1_test_client):
    resp = v1_test_client.get(
        "v1/VIP/-1", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@respx.mock
def test_current_iso_dt_rate_limits(rate_limit_1_per_minute, v1_test_client):
    # Requests with the same tokens should invoke rate limiter
    resp = v1_test_client.get(
        "v1/now", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_200_OK

    resp = v1_test_client.get(
        "v1/now", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # Request with a different token should pass
    resp = v1_test_client.get(
        "v1/now", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[1]}"}
    )
    assert resp.status_code == status.HTTP_200_OK


@respx.mock
def test_track_location_db_server_data_missing(v1_test_client):
    respx.get(settings.DB_SERVER_URL + "/1").mock(
        return_value=Response(
            status_code=status.HTTP_404_NOT_FOUND, json={"test": "test"}
        )
    )

    resp = v1_test_client.get(
        "v1/VIP/1", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@respx.mock
def test_track_location_db_server_timeout(v1_test_client):
    respx.get(settings.DB_SERVER_URL + "/1").mock(side_effect=httpx.ReadTimeout)

    resp = v1_test_client.get(
        "v1/VIP/1", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@respx.mock
def test_track_location_success(v1_test_client):
    respx.get(settings.DB_SERVER_URL + "/1").mock(
        return_value=Response(
            status_code=status.HTTP_200_OK, json={"latitude": "1", "longitude": "2"}
        )
    )

    resp = v1_test_client.get(
        "v1/VIP/1", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_200_OK


@respx.mock
def test_track_location_cache(v1_test_client):
    # First call failed, shouldn't be cached
    respx.get(settings.DB_SERVER_URL + "/2").mock(side_effect=httpx.ReadTimeout)

    resp = v1_test_client.get(
        "v1/VIP/2", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Second call was successful
    respx.get(settings.DB_SERVER_URL + "/2").mock(
        return_value=Response(status_code=200, json={"latitude": "1", "longitude": "2"})
    )

    resp = v1_test_client.get(
        "v1/VIP/2", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_200_OK

    # Third call should be taken from cache
    respx.get(settings.DB_SERVER_URL + "/2").mock(
        return_value=Response(status_code=200, json={"latitude": "2", "longitude": "3"})
    )

    resp = v1_test_client.get(
        "v1/VIP/2", headers={"Authorization": f"Bearer {settings.TEST_API_KEYS[0]}"}
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"source": "vip-db", "gpsCoords": {"lat": 1.0, "long": 2.0}}
