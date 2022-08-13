from pydantic import BaseModel
from datetime import datetime


class CurrentUnixEpochISO(BaseModel):
    """Unix epoch in ISO format."""

    now: datetime

