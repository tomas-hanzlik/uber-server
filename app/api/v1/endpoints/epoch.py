from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette import status

from app.api import deps
from app.schemas.msg import ErrorDetail
from app.schemas.time import CurrentUnixEpochISO

router = APIRouter()

RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorDetail},
}

@router.get(
    "/now",
    dependencies=[Depends(deps.api_key_auth)],
    response_model=CurrentUnixEpochISO,
    responses=RESPONSES,
)
async def current_unix_epoch():
    return {"now": datetime.now(timezone.utc).isoformat(timespec="seconds")}
