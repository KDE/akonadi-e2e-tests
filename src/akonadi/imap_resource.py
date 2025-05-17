from logging import getLogger
import pytest
from sdbus import DbusInterfaceCommonAsync, dbus_method_async, DbusUnprivilegedFlag

from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.dbus.interfaces.org_kde_akonadi_imap_settings import (
    OrgKdeAkonadiImapSettingsInterface,
)
from src.akonadi.client import AkonadiClient, Collection, Item

log = getLogger(__name__)


class WalletIface(
    DbusInterfaceCommonAsync, interface_name="org.kde.Akonadi.Imap.Wallet"
):
    @dbus_method_async(
        input_signature="s",
        result_signature="",
        result_args_names="password",
        flags=DbusUnprivilegedFlag,
        method_name="setPassword",
    )
    async def set_password(self, password: str) -> None:
        pass


class ImapResource:
    RESOURCE_TYPE = "akonadi_imap_resource"

    def __init__(
        self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, instance_id: str
    ) -> None:
        self._dbus = dbus
        self._instance_id = instance_id
        self._akonadi_client = akonadi_client

    @classmethod
    async def create(
        cls, akonadi_client: AkonadiClient, dbus: AkonadiDBus
    ) -> "ImapResource":
        log.debug("Creating IMAP Resource via D-Bus")
        instance_id = await dbus.agent_manager_interface.create_agent_instance(
            cls.RESOURCE_TYPE
        )

        await dbus.wait_for_service(dbus.agent_service_name(instance_id), 10)

        return ImapResource(akonadi_client, dbus, instance_id)

    async def configure(
        self, host: str, port: int, username: str, password: str
    ) -> None:
        settings = OrgKdeAkonadiImapSettingsInterface.new_proxy(
            self._dbus.resource_service_name(self._instance_id),
            "/Settings",
            self._dbus.client,
        )

        await settings.set_imap_server(host)
        await settings.set_imap_port(port)
        await settings.set_safety("PLAIN")
        await settings.set_authentication(1)
        await settings.set_user_name(username)

        wallet = WalletIface.new_proxy(
            self._dbus.resource_service_name(self._instance_id),
            "/Settings",
            self._dbus.client,
        )
        await wallet.set_password(password)

        await settings.save()

        # Force-reload the config
        await self._dbus.agent_interface(self._instance_id).reconfigure()

    async def synchronize(self) -> None:
        log.debug("Synchronizing IMAP Resource via D-Bus")
        resource = self._dbus.resource_interface(self._instance_id)
        await resource.synchronize_collection_tree()
        await anext(resource.collection_tree_synchronized.catch())

        await resource.synchronize()
        await anext(resource.synchronized.catch())
        log.debug("IMAP Resource synchronized")

    @property
    def instance_id(self) -> str:
        return self._instance_id

    async def resolve_collection(self, collection_name: str) -> Collection:
        path = collection_name.split("/")

        collections = await self._akonadi_client.list_collections(
            parent_id=0, first_level=True
        )
        resource_root = next(
            filter(lambda c: c.resource == self.instance_id, collections), None
        )
        if not resource_root:
            pytest.fail("Resource root collection not found")

        async def resolve_recursive(parent: Collection, path: list[str]):
            if not path:
                return parent

            collections = await self._akonadi_client.list_collections(
                parent_id=parent.id, first_level=True
            )
            collection = next(filter(lambda c: c.name == path[0], collections), None)
            if not collection:
                pytest.fail(
                    f"Collection {collection_name} not found: {path[0]} does not exist!"
                )

            return await resolve_recursive(collection, path[1:])

        return await resolve_recursive(resource_root, path)

    async def sync_collection(self, collection_name: str) -> None:
        collection = await self.resolve_collection(collection_name)
        await self._dbus.resource_interface(self._instance_id).synchronize_collection(
            collection.id, recursive=False
        )

    async def list_collections(self) -> list[Collection]:
        collections = await self._akonadi_client.list_collections(
            parent_id=0, first_level=True
        )
        resource_root = next(
            filter(lambda c: c.resource == self.instance_id, collections), None
        )
        if not resource_root:
            pytest.fail("Resource root collection not found")

        return await self._akonadi_client.list_collections(parent_id=resource_root.id)

    async def list_items(self, collection_name_or_id: str | int) -> list[Item]:
        if isinstance(collection_name_or_id, str):
            collection = await self.resolve_collection(collection_name_or_id)
            if not collection:
                pytest.fail(f"Collection {collection_name_or_id} not found")

            collection_id = collection.id
        else:
            collection_id = int(collection_name_or_id)

        return await self._akonadi_client.list_items(collection_id=collection_id)
