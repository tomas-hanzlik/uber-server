import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas.location import DbGpsCoordinates


class InvalidDBDataException(Exception):
    ...


async def db_server_fetch_location(point_in_time: int) -> DbGpsCoordinates:
    """Fetch location data from DB server

    Args:
        point_in_time: Point in time for which we want location

    Returns:
        Dict with location data

    Raises:
        InvalidDBDataException - Couldn't process data from DB server
    """
    async with httpx.AsyncClient(timeout=settings.DB_SERVER_TIMEOUT) as client:
        response = await client.get(f"{settings.DB_SERVER_URL}/{point_in_time}")
        response.raise_for_status()

        try:
            # Validation. Might be removed, only due to reliability of the DB server
            return DbGpsCoordinates(**response.json())
        except ValidationError as e:
            raise InvalidDBDataException("db_server.invalid_data") from e
