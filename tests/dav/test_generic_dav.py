# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from caldav.collection import Principal

from src.akonadi.dav_resource import DAVResource
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import DavCalendarFactory, DavEventFactory


def test_initial_sync(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    """
    Starting a first full sync leads to all the items and collections being replicated in the akonadi server
    """
    DavCalendarFactory.create(nb_items=5)
    DavCalendarFactory.create(nb_items=10)
    DavEventFactory.create_batch(10, calendar="Default Calendar")
    groupware_resource.synchronize()
    assert (
        len(groupware_resource.list_collections()) == 4
    )  # parent collection + Default calendar + 2 calendars
    assert len(dav_principal.calendars()) == 3
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_list_calendars(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    """
    Test that the initial setup has synced url/name between the server and the resource
    """
    DavCalendarFactory.create(nb_items=5)
    groupware_resource.synchronize()

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_initial_sync_push_notifications(
    dav_push_notifications_principal: Principal, groupware_push_notifications_resource: DAVResource
) -> None:
    """
    Starting a first full sync leads to all the items and collections being replicated in the akonadi server
    """
    DavCalendarFactory.create(nb_items=5)
    DavCalendarFactory.create(nb_items=10)
    DavEventFactory.create_batch(10, calendar="Default Calendar")
    groupware_push_notifications_resource.synchronize()
    assert (
        len(groupware_push_notifications_resource.list_collections()) == 4
    )  # parent collection + Default calendar + 2 calendars
    assert len(dav_push_notifications_principal.calendars()) == 3
    assert_all_collections_are_equals(
        dav_push_notifications_principal, groupware_push_notifications_resource
    )


def test_list_calendars_push_notifications(
    dav_push_notifications_principal: Principal, groupware_push_notifications_resource: DAVResource
) -> None:
    """
    Test that the initial setup has synced url/name between the server and the resource
    """
    DavCalendarFactory.create(nb_items=5)
    groupware_push_notifications_resource.synchronize()

    assert_all_collections_are_equals(
        dav_push_notifications_principal, groupware_push_notifications_resource
    )
