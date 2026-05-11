# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import timedelta
from logging import getLogger

import pytest
from caldav.collection import Principal
from caldav.elements import dav
from caldav.lib.error import NotFoundError
from icalendar import Calendar

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.utils import AkonadiUtils, WaitJobError
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import (
    AkonadiEventFactory,
    DavCalendarFactory,
    DavEventFactory,
    fake,
)
from src.test import wait_until

log = getLogger(__name__)


def test_offline_remove_collection_and_add_event(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Removing a collection from the akonadi server, adding an item to the collection on the server, nothing happens
    When the resource is set online, the change is replayed on the server and the collection is removed (including the newly added item)
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)
    initial_collections = groupware_resource.list_collections()
    collection = groupware_resource.collection_from_display_name(calendar.name)

    groupware_resource.set_online(False)

    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
        groupware_resource.delete_collection(collection.name())
    DavEventFactory.create(calendar=calendar.name)

    # Nothing happens
    assert dav_principal.calendar(calendar.name)
    assert len(groupware_resource.list_collections()) == len(initial_collections) - 1
    assert calendar.name not in [c.displayName() for c in groupware_resource.list_collections()]

    groupware_resource.set_online(True)

    with pytest.raises(NotFoundError):
        dav_principal.calendar(calendar.name)
    assert len(groupware_resource.list_collections()) == len(initial_collections) - 1
    assert calendar.name not in [c.displayName() for c in groupware_resource.list_collections()]
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.xfail(
    reason="Akonadi BUG? The akonadi collection is not renamed. https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/105",
    strict=True,
)
def test_offline_rename_collection_server_and_resource(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Renaming a collection in the akonadi server, renaming the same collection under another name on the server, nothing happens
    When the resource is set online, the collection in the akonadi server is renamed with the name given on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    initial_collections = groupware_resource.list_collections()
    collection = groupware_resource.collection_from_display_name(calendar.name)
    resource_new_name = f"{calendar.name}{fake.word()}1"
    server_new_name = f"{calendar.name}{fake.word()}2"

    groupware_resource.set_online(False)

    groupware_resource.update_collection_displayname(collection.name(), resource_new_name)
    dav_principal.calendar(calendar.name).set_properties([dav.DisplayName(server_new_name)])

    # Nothing changed
    assert groupware_resource.collection_from_display_name(resource_new_name)
    assert dav_principal.calendar(server_new_name)

    groupware_resource.set_online(True)

    assert len(groupware_resource.list_collections()) == len(initial_collections)
    assert groupware_resource.collection_from_display_name(server_new_name)
    assert dav_principal.calendar(server_new_name)
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_conflict_remove_collection(
    dav_principal: Principal, groupware_resource: DAVResource, akonadi_client: AkonadiClient
) -> None:
    """
    Removing an item from a collection in the akonadi server, removing the collection on the server, nothing happens
    When the resource is set online, the collection is removed from the akonadi server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) > 0
    item = items[0]

    groupware_resource.set_online(False)

    akonadi_client.delete_item(item.id())

    dav_calendar = dav_principal.calendar(calendar.name)

    dav_calendar.delete()
    wait_until(
        lambda: calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert collection.id() in [c.id() for c in groupware_resource.list_collections()]
    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) - 1
    assert item.id() not in [i.id() for i in groupware_resource.list_items(collection.name())]

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.id() not in [c.id() for c in groupware_resource.list_collections()]


random_dtsart = fake.future_datetime()

changed_field_data = [
    pytest.param("DESCRIPTION", fake.paragraph(), fake.boolean(), id="description"),
    pytest.param("SUMMARY", fake.sentence(), fake.boolean(), id="summary"),
    pytest.param(
        "DTSTART", fake.future_datetime().strftime("%Y%m%dT%H%M%S"), fake.boolean(), id="dtstart"
    ),
    pytest.param(
        "DTEND",
        fake.date_time_between(
            start_date=random_dtsart, end_date=random_dtsart + timedelta(hours=8)
        ).strftime("%Y%m%dT%H%M%S"),
        True,
        id="dtend",
    ),
    pytest.param("DURATION", f"PT{fake.random_int(min=1, max=8)}H", False, id="duration"),
]


@pytest.mark.parametrize("field, new_value, use_dtend", changed_field_data)
def test_update_item_locally_in_collection_removed_on_server(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
    field: str,
    new_value: str,
    use_dtend: bool,
) -> None:
    """
    Changing the content of an item in the akonadi server, removing the collection on the server, nothing happens,
    when the resource is set online, the collection is removed from the akonadi server
    """
    calendar = DavCalendarFactory.create()
    DavEventFactory.create(calendar=calendar.name, use_dtend=use_dtend, dtstart=random_dtsart)

    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) > 0
    item = items[0]

    groupware_resource.set_online(False)

    payload = bytes(item.payloadData()).decode()
    item_calendar = Calendar.from_ical(payload)
    [item_event] = item_calendar.walk("VEVENT")
    item_event[field] = new_value
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    dav_calendar = dav_principal.calendar(calendar.name)

    dav_calendar.delete()
    wait_until(
        lambda: calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    # Since we're still offline, ensure no change was made locally
    assert collection.id() in [c.id() for c in groupware_resource.list_collections()]

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.remoteId() not in [c.remoteId() for c in akonadi_client.list_collections()]


@pytest.mark.xfail(
    reason="Items from deleted collections are still present in the resource. https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/104",
    strict=True,
)
def test_conflict_add_item_akonadi_remove_collection_server(
    dav_principal: Principal, groupware_resource: DAVResource, akonadi_client: AkonadiClient
) -> None:
    """
    Adding an item to a collection in the akonadi server, removing the collection on the server, nothing happens;
    when the resource is set online, the collection is removed from the akonadi server, the item is removed as well
    """
    initial_factory = DavCalendarFactory.create()
    groupware_resource.synchronize()
    collection = groupware_resource.collection_from_display_name(initial_factory.name)
    calendar_to_delete = dav_principal.calendar(initial_factory.name)

    groupware_resource.set_online(False)

    # Add an event in Akonadi, check it exists in the resource and not in the server
    AkonadiEventFactory.create(calendar=initial_factory.name)
    items_from_collection_to_delete = groupware_resource.list_items(collection.id())

    assert len(groupware_resource.list_items(collection.id())) == len(initial_factory.events) + 1
    assert len(dav_principal.calendar(initial_factory.name).get_events()) == len(
        initial_factory.events
    )

    # Delete collection server side, check collection is deleted in the server and not in the resource
    calendar_to_delete.delete()

    assert initial_factory.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert initial_factory.name in [c.displayName() for c in groupware_resource.list_collections()]

    groupware_resource.set_online(True)

    # Check collection is deleted on both sides
    assert initial_factory.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert initial_factory.name not in [
        c.displayName() for c in groupware_resource.list_collections()
    ]

    # Check all items are deleted on akonadi side
    for item in items_from_collection_to_delete:
        with pytest.raises(WaitJobError):
            akonadi_client.item_by_id(item.id(), False)

    # Check other collections are still there
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_add_item_remotely_to_collection_removed_locally(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Adding an item to a collection on the server, removing the collection in akonadi server, nothing happens, when the
    resource is set online, the collection is removed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    groupware_resource.set_online(False)

    DavEventFactory.create(calendar=calendar.name)

    collection = groupware_resource.collection_from_display_name(calendar.name)

    # No change was replicated on the server
    assert dav_principal.calendar(calendar.name) is not None
    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
        groupware_resource.delete_collection(collection.remoteId())

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.remoteId() not in [
        c.remoteId() for c in groupware_resource.list_collections()
    ]
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_delete_item_remotely_on_collection_removed_locally(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection on the server, removing the collection in akonadi server, nothing happens, when
    the resource is set online, the collection is removed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    groupware_resource.set_online(False)

    event_to_delete = dav_principal.calendar(calendar.name).events()[0]
    event_to_delete.delete()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert collection is not None
    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
        akonadi_client.delete_collection(collection.id())

    # No change was replicated on the server
    assert dav_principal.calendar(calendar.name) is not None

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.remoteId() not in [
        c.remoteId() for c in groupware_resource.list_collections()
    ]
    assert_all_collections_are_equals(dav_principal, groupware_resource)
