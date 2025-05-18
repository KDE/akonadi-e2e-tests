# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from camel_converter import to_camel


class Item(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int
    remote_id: str | None = None
    gid: str | None = None
    mime_type: str
    size: int
    modification_time: datetime
    flags: list[str]
