import httpx
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi_cache.decorator import cache
from loguru import logger
from starlette import status

from app.api import deps
from app.schemas.location import GpsCoordinates, Location
from app.schemas.msg import ErrorDetail
from app.utils import InvalidDBDataException, db_server_fetch_location

router = APIRouter()


RESPONSES = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorDetail},
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorDetail},
    status.HTTP_404_NOT_FOUND: {"model": ErrorDetail},
}


@router.get(
    "/VIP/{point_in_time}",
    dependencies=[Depends(deps.api_key_auth)],
    response_model=Location,
    responses=RESPONSES,
)
@cache(expire=5 * 60)
async def track_location(
    point_in_time: int = Path(title="Get coordinates for given point in time", gt=0),
):
    try:
        data = await db_server_fetch_location(point_in_time)
        return Location(
            gpsCoords=GpsCoordinates(lat=data.latitude, long=data.longitude)
        )
    except (httpx.RequestError, httpx.HTTPStatusError, InvalidDBDataException) as e:
        # Point in time not found on DB server
        if (
            isinstance(e, httpx.HTTPStatusError)
            and e.response.status_code == status.HTTP_404_NOT_FOUND
        ):
            raise HTTPException(status_code=404, detail="Record not found")

        logger.debug("db_server.error", exc=e)
        raise HTTPException(
            status_code=500, detail="Cannot access required data, please try later"
        )
