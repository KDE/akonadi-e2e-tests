# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from caldav.collection import Principal

from src.akonadi.dav_resource import DAVResource
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import DavCalendarFactory, DavEventFactory


def test_offline_remove_items(dav_principal: Principal, groupware_resource: DAVResource):
    """
    Removing an item from a collection on the server, nothing happens, when the resource is set online, the removed item is also removed in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    calendar = DavCalendarFactory.create(nb_items=5)
    DavEventFactory.create_batch(10, calendar="Default Calendar")
    groupware_resource.synchronize()
    initial_events_from_custom_calendar = dav_principal.calendar(calendar.name).get_events()
    initial_events_from_default_calendar = dav_principal.calendar("Default Calendar").get_events()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    events_to_remove_default_calendar = initial_events_from_default_calendar[:3]
    events_to_remove_custom_calendar = initial_events_from_custom_calendar[:2]

    groupware_resource.set_online(False)

    for event in events_to_remove_default_calendar:
        event.delete()
    for event in events_to_remove_custom_calendar:
        event.delete()

    # assert nothing happened on akonadi side
    unsynced_custom_collection = groupware_resource.collection_from_display_name(calendar.name)
    unsynced_custom_items = groupware_resource.list_items(unsynced_custom_collection.id())
    assert len(unsynced_custom_items) == len(initial_events_from_custom_calendar)

    unsynced_default_collection = groupware_resource.collection_from_display_name(
        "Default Calendar"
    )
    unsynced_default_items = groupware_resource.list_items(unsynced_default_collection.id())
    assert len(unsynced_default_items) == len(initial_events_from_default_calendar)

    groupware_resource.set_online(True)

    # assert synchronization is done
    synced_custom_collection = groupware_resource.collection_from_display_name(calendar.name)
    synced_custom_items = groupware_resource.list_items(synced_custom_collection.id())
    assert len(synced_custom_items) == len(initial_events_from_custom_calendar) - len(
        events_to_remove_custom_calendar
    )

    synced_default_collection = groupware_resource.collection_from_display_name("Default Calendar")
    synced_default_items = groupware_resource.list_items(synced_default_collection.id())
    assert len(synced_default_items) == len(initial_events_from_default_calendar) - len(
        events_to_remove_default_calendar
    )
    assert_all_collections_are_equals(dav_principal, groupware_resource)
