import pytest
from src.akonadi.imap_resource import ImapResource
from src.imap.client import ImapClient


def compare_flags(flags1: list[str], flags2: list[str]) -> bool:
    return {f.lower() for f in flags1} == {f.lower() for f in flags2}


async def check_collection_in_sync(
    name: str, imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await imap_resource.sync_collection(name)
    items = await imap_resource.list_items(name)
    items.sort(key=lambda i: i.id)

    messages = await imap_client.list_messages("INBOX")
    messages.sort(key=lambda m: m.seq)

    assert len(messages) == len(items)

    for msg, item in zip(messages, items):
        assert msg.uid == int(item.remote_id or -1)
        assert compare_flags(msg.flags, item.flags)


@pytest.mark.asyncio
async def test_initial_sync(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("INBOX", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_change(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("INBOX", imap_resource, imap_client)

    await imap_client.add_flag("INBOX", 1, "$TestFlag")
    await imap_resource.sync_collection("INBOX")

    await check_collection_in_sync("INBOX", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("INBOX", imap_resource, imap_client)

    await imap_client.remove_message("INBOX", 1)
    await imap_resource.sync_collection("INBOX")

    await check_collection_in_sync("INBOX", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_added_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("INBOX", imap_resource, imap_client)

    await imap_client.add_new_message("INBOX")
    await imap_resource.sync_collection("INBOX")

    await check_collection_in_sync("INBOX", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("INBOX", imap_resource, imap_client)

    await imap_client.add_flag("INBOX", 2, "$TestFlag")
    await imap_client.remove_message("INBOX", 1)
    await imap_resource.sync_collection("INBOX")

    await check_collection_in_sync("INBOX", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("INBOX", imap_resource, imap_client)

    await imap_client.add_flag("INBOX", 2, "$TestFlag")
    await imap_client.add_new_message("INBOX")
    await imap_resource.sync_collection("INBOX")

    await check_collection_in_sync("INBOX", imap_resource, imap_client)
