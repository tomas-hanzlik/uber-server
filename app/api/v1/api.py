from fastapi import APIRouter

from app.api.v1.endpoints import location
from app.api.v1.endpoints import epoch

api_router = APIRouter()
api_router.include_router(location.router, tags=["location"])
api_router.include_router(epoch.router, tags=["epoch"])
