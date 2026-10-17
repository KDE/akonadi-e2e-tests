# SPDX-FileCopyrightText: 2026 David Faure <faure@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from collections.abc import Generator
from urllib.parse import unquote

import pytest
from caldav.collection import Principal

from src.akonadi.dav_resource import DAVResource
from src.dav.renaming_server import RenamingRadicaleServer
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import AkonadiEventFactory, DavCalendarFactory
from src.test import wait_until


@pytest.fixture(scope="module")
def dav_server_session() -> Generator[RenamingRadicaleServer]:
    server = RenamingRadicaleServer()
    server.start()
    yield server
    server.stop()


def test_akonadi_add_item_renamed_by_server(
    dav_server: RenamingRadicaleServer, dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    The server stores an item added in akonadi under another name, given in a path-only
    Location header: the akonadi item gets that name as remote ID, and the next sync
    doesn't add a duplicate
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    AkonadiEventFactory.create(calendar=calendar.name)
    collection = groupware_resource.collection_from_display_name(calendar.name)
    wait_until(
        lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) + 1
    )
    groupware_resource.wait_resource_is_idle()
    groupware_resource.synchronize()

    assert len(dav_server.renamed) == 1
    stored_path = dav_server.renamed[0][1]
    items = groupware_resource.list_items(collection.id())
    assert len(items) == len(calendar.events) + 1
    assert all(item.remoteId() for item in items)
    assert any(unquote(item.remoteId()).endswith(unquote(stored_path)) for item in items)
    assert_all_collections_are_equals(dav_principal, groupware_resource)
