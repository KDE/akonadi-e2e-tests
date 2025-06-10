import pytest

from src.akonadi.dav_resource import DAVResource
from src.dav.client import DavClient

@pytest.mark.asyncio
async def test_list_calendars(
    dav_client: DavClient, groupware_resource: DAVResource
) -> None:
    server_calendars = await dav_client.list_calendars()

    akonadi_calendars = await groupware_resource.list_collections()

    assert len(server_calendars) == len(akonadi_calendars)

    for server_calendar, akonadi_calendar in zip(server_calendars, akonadi_calendars):
        assert server_calendar.name == akonadi_calendar.name
