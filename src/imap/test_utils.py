# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from AkonadiCore import Akonadi  # type: ignore

from src.akonadi.imap_resource import ImapResource
from src.imap.client import ImapClient

log = getLogger(__name__)


def compare_flags(flags1: list[str], flags2: list[str]) -> bool:
    # Ignore the \Recent flag, since it's special and is assigned dynamically
    # by the server, so it's likely that only either Akonadi or the IMAP client
    # in the test will see it.
    # We don't interpret or treat it specially anyway, so it doesn't matter too much.
    def to_set(flags: list[str]) -> set[str]:
        return {f.lower() for f in flags if f != r"\Recent"}

    return to_set(flags1) == to_set(flags2)


async def check_collection_in_sync(
    name: str, imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await imap_resource.sync_collection(name)
    items = imap_resource.list_items(name)
    items.sort(key=lambda i: int(i.remoteId() or -1))

    messages = await imap_client.list_messages(name)
    messages.sort(key=lambda m: m.uid)

    assert len(messages) == len(items)

    for msg, item in zip(messages, items, strict=False):
        log.info("Comparing message %s and item %s", msg.uid, item.remoteId())
        assert msg.uid == int(item.remoteId() or -1)
        log.info("Comparing flags: %s and %s", msg.flags, item.flags())
        assert compare_flags(msg.flags, [bytes(f).decode() for f in item.flags()])


async def message_added(imap_client: ImapClient, mailbox: str, seq: int) -> bool:
    return await imap_client.fetch_message(mailbox, seq=seq) is not None


async def message_deleted(imap_client: ImapClient, item: Akonadi.Item, mailbox: str) -> bool:
    assert item.remoteId() is not None
    await imap_client.expunge(mailbox)
    return await imap_client.fetch_message(mailbox, uid=int(item.remoteId())) is None
