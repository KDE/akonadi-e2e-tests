from enum import Flag
from pydantic import BaseModel, field_validator

from .item import Item


class Rights(Flag):
    READ_ONLY = (0,)
    CAN_CHANGE_ITEM = 0x1
    CAN_CREATE_ITEM = 0x2
    CAN_DELETE_ITEM = 0x4
    CAN_CHANGE_COLLECTION = 0x8
    CAN_CREATE_COLLECTION = 0x10
    CAN_DELETE_COLLECTION = 0x20
    CAN_LINK_ITEM = 0x40
    CAN_UNLINK_ITEM = 0x80


class Collection(BaseModel):
    id: int
    name: str
    remote_id: str | None = None
    parent_id: int
    resource: str
    content_mime_types: list[str]
    rights: Rights
    is_virtual: bool
    child_collections: list["Collection"]
    child_items: list[Item]

    @classmethod
    @field_validator("rights", mode="before")
    def validate_rights(cls, v: list[str]) -> Rights:
        r = set(v)
        rights = Rights.READ_ONLY
        if "ReadOnly" in r:
            rights |= Rights.READ_ONLY
        if "CanChangeItem" in r:
            rights |= Rights.CAN_CHANGE_ITEM
        if "CanCreateItem" in r:
            rights |= Rights.CAN_CREATE_ITEM
        if "CanDeleteItem" in r:
            rights |= Rights.CAN_DELETE_ITEM
        if "CanChangeCollection" in r:
            rights |= Rights.CAN_CHANGE_COLLECTION
        if "CanCreateCollection" in r:
            rights |= Rights.CAN_CREATE_COLLECTION
        if "CanDeleteCollection" in r:
            rights |= Rights.CAN_DELETE_COLLECTION
        return rights


class ListCollectionsResult(BaseModel):
    collections: list[Collection]


class ListItemsResult(BaseModel):
    items: list[Item]
