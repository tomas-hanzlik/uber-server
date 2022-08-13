from typing import List, Union

from pydantic import AnyHttpUrl, BaseSettings, SecretStr, validator, RedisDsn


class Settings(BaseSettings):
    DEBUG: bool = True
    PROJECT_NAME: str = "UberServer"
    API_V1_PREFIX: str = "/v1"

    # Global rate limit for all endpoints
    RATE_LIMIT: str = "200/minute"

    # API keys for v1 API endpoints
    API_KEYS: str | list[SecretStr] = []

    # API used in tests only. As a plain string to be able to pass the secret to endpoint auth in tests.
    # (SecretStr hides the real value)
    TEST_API_KEYS: list[str] = ["test_api_key1", "test_api_key2"]

    # Maximum timeout for DB server
    DB_SERVER_TIMEOUT: int = 3
    DB_SERVER_URL: AnyHttpUrl

    # Redis url used for caching and rate limits
    REDIS_URI: RedisDsn | None  # If None, in memory cache will be used

    @validator("API_KEYS", pre=True)
    def _assemble_api_keys(cls, value: str | list[str]) -> Union[List[str], str]:
        # Parse API keys from env. var. string
        if isinstance(value, str):
            return [i.strip() for i in value.split(",")]
        elif isinstance(value, (list, str)):
            return value
        raise ValueError(value)

    class Config:
        case_sensitive = True
        env_prefix = "UBER_SERVER_"


settings = Settings()
