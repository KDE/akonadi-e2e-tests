# SPDX-FileCopyrightText: 2026 MICHEL Dominique <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import pytest
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Principal

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.utils import AkonadiUtils
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import (
    AkonadiCalendarFactory,
    AkonadiEventFactory,
    DavCalendarFactory,
)
from src.test import wait_until


@pytest.mark.xfail(
    reason="The test is failing because collectionAdded is not implemented in dav resource"
)
def test_akonadi_sync_add_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Adding a collection in the akonadi server, the change is replayed on the server
    """
    calendar = AkonadiCalendarFactory.create()
    groupware_resource.synchronize()

    wait_until(
        lambda: calendar.name in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_sync_remove_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Removing a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    wait_until(
        lambda: calendar.name in [c.displayName() for c in groupware_resource.list_collections()]
    )

    collection = groupware_resource.collection_from_display_name(calendar.name)
    job = Akonadi.CollectionDeleteJob(collection)
    AkonadiUtils.wait_for_job(job)
    wait_until(
        lambda: calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_sync_add_item(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    """
    Adding an item to a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    AkonadiEventFactory.create(calendar=calendar.name)
    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) + 1
    groupware_resource.synchronize()

    wait_until(
        lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) + 1
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_sync_remove_item(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.id())
    item = items[0]

    akonadi_client.delete_item(item.id())

    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) - 1

    groupware_resource.synchronize()
    wait_until(
        lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) - 1
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)
