from pydantic import BaseModel


class GpsCoordinates(BaseModel):
    """Alternative coordinates format - used for response representation."""

    lat: float
    long: float


class Location(BaseModel):
    """Location that contains DB source and GPS coordinates"""

    source: str = "vip-db"
    gpsCoords: GpsCoordinates


class DbGpsCoordinates(BaseModel):
    """DB coordinates format saved in DB"""

    latitude: float
    longitude: float
