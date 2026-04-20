# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from collections.abc import Iterable
from logging import getLogger

from AkonadiCore import Akonadi  # type: ignore
from imap_tools import AND, A, BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.factories.email_factory import ImapEmailFactory, ImapFolderFactory
from src.imap.mailbox_with_original_payload import MailMessageWithOriginalPayload

log = getLogger(__name__)


def compare_flags(flags1: Iterable[str], flags2: list[str]) -> bool:
    # Ignore the \Recent flag, since it's special and is assigned dynamically
    # by the server, so it's likely that only either Akonadi or the IMAP client
    # in the test will see it.
    # We don't interpret or treat it specially anyway, so it doesn't matter too much.
    def to_set(flags: Iterable[str]) -> set[str]:
        return {f.lower() for f in flags if f != r"\Recent"}

    return to_set(flags1) == to_set(flags2)


def assert_collection_equal_mailbox(
    name: str, imap_resource: ImapResource, imap_client: BaseMailBox, payload_test: bool = True
) -> None:
    items = imap_resource.list_items(name)
    items.sort(key=lambda i: i.remoteId() or "-1")

    imap_client.folder.set(name)
    messages = list(imap_client.fetch(mark_seen=False))
    messages.sort(key=lambda m: m.uid or "-1")

    assert len(messages) == len(items)

    for msg, item in zip(messages, items, strict=False):
        log.info("Comparing message %s and item %s", msg.uid, item.remoteId())
        assert msg.uid == item.remoteId()
        log.info("Comparing flags: %s and %s", msg.flags, item.flags())
        assert compare_flags(msg.flags, [bytes(f).decode() for f in item.flags()])
        if payload_test:
            assert_payload_are_equal(item, msg)  # type: ignore


def message_added(imap_client: BaseMailBox, mailbox: str, uid: str) -> bool:
    imap_client.folder.set(mailbox)
    return bool(list(imap_client.fetch(A(uid=[uid]), mark_seen=False)))


def message_deleted(imap_client: BaseMailBox, item: Akonadi.Item, mailbox: str) -> bool:
    assert item.remoteId() is not None
    imap_client.folder.set(mailbox)
    imap_client.expunge()
    return not bool(list(imap_client.fetch(A(uid=item.remoteId()), mark_seen=False)))


def has_flag(imap_client: BaseMailBox, item: Akonadi.Item, mailbox: str, flag: str) -> bool:
    assert item.remoteId() is not None
    imap_client.folder.set(mailbox)
    [imap_mail] = imap_client.fetch(AND(uid=item.remoteId()), mark_seen=False)
    return flag in imap_mail.flags


def assert_payload_are_equal(
    akonadi_message: Akonadi.Item, imap_message: MailMessageWithOriginalPayload
) -> None:
    akonadi_payload = akonadi_message.payloadData().data().decode()
    imap_payload = imap_message.raw_message_data.decode().replace("\r\n", "\n")
    assert akonadi_payload == imap_payload


def assert_partial_sync(
    initial_items: list[Akonadi.Item],
    current_items: list[Akonadi.Item],
    updated_items: list[Akonadi.Item],
) -> None:
    """
    Check between two item lists that only the items to check have been synced.
    Note that we do not really check whether the IMAP server or Akonadi server sent only the updated items; instead, we check on the Akonadi side that only the updated items have been sync.
    The only available field to perform this check is the revision.

    :param initial_items: the items before the sync
    :param current_items: the items after the sync
    :param updated_items: the items that should have been updated
    """

    updated_items_id = [item.id() for item in updated_items]

    for initial_item, current_item in zip(initial_items, current_items, strict=False):
        # handle updated items
        if initial_item.id() in updated_items_id:
            assert current_item.revision() > initial_item.revision()
            assert (
                current_item.modificationTime().toMSecsSinceEpoch()
                > initial_item.modificationTime().toMSecsSinceEpoch()
            )
        # handle added items
        elif initial_item.id() not in updated_items_id:
            assert current_item.revision() == 0
            assert current_item.modificationTime().toMSecsSinceEpoch() is not None
        # handle unchanged items
        else:
            assert current_item.revision() == initial_item.revision()
            assert (
                current_item.modificationTime().toMSecsSinceEpoch()
                == initial_item.modificationTime().toMSecsSinceEpoch()
            )


def old_prepare(imap_client: BaseMailBox, imap_resource: ImapResource) -> None:
    """
    Need to be deleted after migrating all tests to factory boys
    """
    folder_to_create = ["Trash", "Sent", "Templates", "TestEmpty", "Test", "Test2"]
    for name in folder_to_create:
        ImapFolderFactory.create(name=name, nb_items=0)
    assert len(imap_client.folder.list()) == len(folder_to_create) + 1, (
        "Failed to create all folders"
    )  # + 1 for INBOX

    for mailbox in ["INBOX", "Test", "Test2"]:
        ImapEmailFactory.create_batch(2, folder=mailbox)

    log.info("IMAP server populated with messages")
    imap_resource.synchronize()
