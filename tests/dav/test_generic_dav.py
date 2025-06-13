# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from urllib.parse import unquote_plus

import pytest

from src.akonadi.dav_resource import DAVResource
from src.dav.client import DavClient


@pytest.mark.asyncio
async def test_list_calendars(
    dav_client: DavClient, groupware_resource: DAVResource
) -> None:
    server_calendars = await dav_client.list_calendars()
    # Skip root collection
    akonadi_calendars = [
        c for c in await groupware_resource.list_collections() if c.parent_id != 0
    ]

    assert len(server_calendars) == len(akonadi_calendars)
    for server_calendar, akonadi_calendar in zip(server_calendars, akonadi_calendars):
        assert unquote_plus(str(server_calendar.url)) == akonadi_calendar.name
