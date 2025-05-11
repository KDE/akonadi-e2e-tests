from datetime import datetime
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str
    remote_id: str | None = None
    parent_id: int
    resource: str
    gid: str | None = None
    mime_type: str
    size: int
    modification_time: datetime
    flags: list[str]
