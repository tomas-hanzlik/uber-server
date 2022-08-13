from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr
from starlette import status
from starlette.requests import Request

from app.config import settings


class CustomHTTPBearerScheme(HTTPBearer):
    """Specify error message and status code"""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        try:
            auth = await super().__call__(request)
        except HTTPException:
            # Catch exception when no header is provided or is in a wrong format
            # + Override wrong status code
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please provide credentials",
            )

        return auth


def api_key_auth(auth: str = Depends(CustomHTTPBearerScheme())):
    """Check if provided api key is valid

    Args:
        auth: User's API key

    Raises:
        HTTPException - To forbid access
    """
    if SecretStr(auth.credentials) not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
