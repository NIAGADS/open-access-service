from typing import Optional

from pydantic import BaseModel


class AppServer(BaseModel):
    url: str
    description: Optional[str] = None


class AppMetadata(BaseModel):
    title: str
    description: str
    summary: str
    terms_of_service: str
    # servers: list[AppServer]
