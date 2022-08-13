import pytest
from pydantic import SecretStr
from starlette.testclient import TestClient

from app.config import settings
from app.app_init import create_app


@pytest.fixture(scope="function")
def rate_limit_1_per_minute():
    old_value = settings.RATE_LIMIT
    settings.RATE_LIMIT = "1/minute"  # Change rate limits
    yield
    settings.RATE_LIMIT = old_value


@pytest.fixture(scope="module")
def v1_test_client():
    # Set a valid token for testing purposes
    settings.API_KEYS = [SecretStr(key) for key in settings.TEST_API_KEYS]

    # Unset REDIS_URI to not be dependant on redis during tests
    settings.REDIS_URI = None

    # Create a new app to allow `pytest_configure` to change the configuration
    client = TestClient(create_app(), base_url="http://v1")
    yield client
