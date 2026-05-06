# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny Lorin <kenny.lorin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.akonadi.utils import WaitJobError
from src.factories.email_factory import AkonadiFolderFactory


@pytest.mark.xfail(
    reason="Deleting the collection does not cascade all the way to items within that collection, "
    "see https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/104"
)
def test_delete_collection_with_one_item_should_delete_item(
    imap_resource: ImapResource,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Deleting a collection through the resource also deletes the items that are within that collection.
    """
    folder = AkonadiFolderFactory.create(nb_items=1)

    pre_update_items_on_resource = imap_resource.list_items(folder.name)

    imap_resource.delete_collection(folder.name)

    assert folder.name not in (c.name() for c in imap_resource.list_collections())
    with pytest.raises(WaitJobError):
        akonadi_client.item_by_id(pre_update_items_on_resource[0].id())
