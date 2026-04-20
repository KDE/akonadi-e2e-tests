# SPDX-FileCopyrightText: 2026 MICHEL Dominique <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from datetime import datetime

from caldav.collection import Principal


from src.dav.dav_utils import create_event
from src.akonadi.dav_resource import DAVResource


def test_resource_add_item_sync(dav_principal: Principal, groupware_resource: DAVResource):
    """
    Adding an item to a collection in the akonadi server, the change is replayed on the server
    """
    collection = groupware_resource.collection_from_display_name("TestEmpty")
    items = groupware_resource.list_items(collection.id())
    assert len(items) == 0

    akonadi_client.add_item(
        collection.id(),
        create_event(datetime.now(), "TestTitle"),
        "application/x-vnd.akonadi.calendar.event",
    )

    items = groupware_resource.list_items(collection.id())
    assert len(items) == 1

    # TODO: wait until message created on server
