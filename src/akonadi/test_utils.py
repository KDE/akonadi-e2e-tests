# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from collections.abc import Iterable
from logging import getLogger

from AkonadiCore import Akonadi  # type: ignore

log = getLogger(__name__)


def compare_flags(flags1: Iterable[str], flags2: list[str]) -> bool:
    # Ignore the \Recent flag, since it's special and is assigned dynamically
    # by the server, so it's likely that only either Akonadi or the IMAP client
    # in the test will see it.
    # We don't interpret or treat it specially anyway, so it doesn't matter too much.
    def to_set(flags: Iterable[str]) -> set[str]:
        return {f.lower() for f in flags if f != r"\Recent"}

    return to_set(flags1) == to_set(flags2)


def assert_akonadi_item_are_equal(item1: Akonadi.Item, item2: Akonadi.Item) -> None:
    assert item1.id() == item2.id()
    item1_payload = item1.payloadData().data().decode()
    item2_payload = item2.payloadData().data().decode()
    assert item1_payload == item2_payload
    assert compare_flags(
        [bytes(f).decode() for f in item1.flags()], [bytes(f).decode() for f in item2.flags()]
    )


def assert_akonadi_items_are_equal(items1: list[Akonadi.Item], items2: list[Akonadi.Item]) -> None:
    items1.sort(key=lambda item: item.id())
    items2.sort(key=lambda item: item.id())
    for item1, item2 in zip(items1, items2, strict=True):
        assert_akonadi_item_are_equal(item1, item2)


def assert_item_sync(initial_item: Akonadi.Item, current_item: Akonadi.Item) -> None:
    """
    Assert item has been sync
    Note that we do not really check whether the IMAP server or Akonadi server sent only the updated items; instead, we check on the Akonadi side that only the update item has been sync.
    The only available fields to perform this check is the revision and modification time.
    :param initial_item: The item before the sync
    :param current_item: The item after the sync
    :return:
    """
    assert current_item.id() == initial_item.id()
    assert current_item.revision() > initial_item.revision()
    assert (
        current_item.modificationTime().toMSecsSinceEpoch()
        > initial_item.modificationTime().toMSecsSinceEpoch()
    )


def assert_item_unsync(initial_item: Akonadi.Item, current_item: Akonadi.Item) -> None:
    """
    Assert item has not been sync
    :param initial_item: The item before the sync
    :param current_item: The item after the sync
    :return:
    """
    assert current_item.id() == initial_item.id()
    assert current_item.revision() == initial_item.revision()
    assert (
        current_item.modificationTime().toMSecsSinceEpoch()
        == initial_item.modificationTime().toMSecsSinceEpoch()
    )
