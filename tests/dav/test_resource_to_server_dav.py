# SPDX-FileCopyrightText: 2026 MICHEL Dominique <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import pytest
from caldav.collection import Principal

from src.akonadi.dav_resource import DAVResource
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import AkonadiCalendarFactory
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
    AkonadiCalendarFactory.create(name="TestTopLevel", nb_items=0)
    groupware_resource.synchronize()

    wait_until(
        lambda: "TestTopLevel" in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)
