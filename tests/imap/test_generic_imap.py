import pytest
from src.akonadi.imap_resource import ImapResource


@pytest.mark.asyncio
async def test_initial_sync(imap_resource: ImapResource) -> None:
    await imap_resource.sync_collection("INBOX")
    items = await imap_resource.list_items("INBOX")
    assert len(items) == 2
