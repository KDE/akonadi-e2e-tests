from enum import Flag
from pydantic import BaseModel, ConfigDict
from camel_converter import to_camel

from .item import Item


class Rights(Flag):
    READ_ONLY = "ReadOnly"
    CAN_CHANGE_ITEM = "CanChangeItem"
    CAN_CREATE_ITEM = "CanCreateItem"
    CAN_DELETE_ITEM = "CanDeleteItem"
    CAN_CHANGE_COLLECTION = "CanChangeCollection"
    CAN_CREATE_COLLECTION = "CanCreateCollection"
    CAN_DELETE_COLLECTION = "CanDeleteCollection"
    CAN_LINK_ITEM = "CanLinkItem"
    CAN_UNLINK_ITEM = "CanUnlinkItem"


class Collection(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int
    name: str
    remote_id: str | None = None
    parent_id: int
    resource: str
    content_mime_types: list[str]
    rights: set[Rights]
    is_virtual: bool
    child_collections: list["Collection"]
    child_items: list[Item]
