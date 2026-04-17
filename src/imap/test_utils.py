# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from AkonadiCore import Akonadi  # type: ignore
from imap_tools import AND, A, BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.akonadi.test_utils import compare_flags
from src.imap.mailbox_with_original_payload import MailMessageWithOriginalPayload

log = getLogger(__name__)


def assert_all_collections_are_equals(
    imap_client: BaseMailBox, imap_resource: ImapResource, payload_test: bool = True
) -> None:
    mailboxes = imap_client.folder.list()
    collections = [c for c in imap_resource.list_collections() if c.parentCollection().id() != 0]

    assert len(mailboxes) == len(collections)
    for mailbox in mailboxes:
        assert_collection_equal_mailbox(mailbox.name, imap_resource, imap_client, payload_test)


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
    return flag.lower() in [flag.lower() for flag in imap_mail.flags]


def assert_payload_are_equal(
    akonadi_message: Akonadi.Item, imap_message: MailMessageWithOriginalPayload
) -> None:
    akonadi_payload = akonadi_message.payloadData().data().decode()
    imap_payload = imap_message.raw_message_data.decode().replace("\r\n", "\n")
    assert akonadi_payload == imap_payload
