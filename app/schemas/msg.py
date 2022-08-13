from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Format of an error response"""

    detail: str
