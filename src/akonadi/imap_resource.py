# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override

import pytest
from AkonadiCore import Akonadi  # type: ignore
from sdbus import DbusInterfaceCommon, DbusUnprivilegedFlag, dbus_method

from src.akonadi.client import AkonadiClient
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.dbus.interfaces.org_kde_akonadi_imap_resource import (
    OrgKdeAkonadiImapResourceBaseInterface,
)
from src.akonadi.dbus.interfaces.org_kde_akonadi_imap_settings import (
    OrgKdeAkonadiImapSettingsInterface,
)
from src.akonadi.resource import Resource
from src.akonadi.utils import AkonadiUtils
from src.kwallet.client import KWalletClient

log = getLogger(__name__)


class WalletIface(DbusInterfaceCommon, interface_name="org.kde.Akonadi.Imap.Wallet"):
    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setPassword",
    )
    def set_password(self, password: str) -> None:
        pass


class ImapResource(Resource):
    RESOURCE_TYPE = "akonadi_imap_resource"

    def __init__(self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, identifier: str) -> None:
        super().__init__(akonadi_client, dbus, identifier)
        self._kwallet_key = f"{self._identifier}_{self.akonadi_client.akonadi_instance_name}rc"

    def configure(self, host: str, port: int, username: str, password: str, delim: str) -> None:
        self.delimiter = delim
        settings = OrgKdeAkonadiImapSettingsInterface(
            self._dbus.resource_service_name(self._identifier),
            "/Settings",
        )

        settings.set_imap_server(host)
        settings.set_imap_port(port)
        settings.set_safety("PLAIN")
        settings.set_authentication(1)
        settings.set_user_name(username)
        settings.set_interval_check_enabled(False)

        wallet = WalletIface(
            self._dbus.resource_service_name(self._identifier),
            "/Settings",
        )
        wallet.set_password(password)

        settings.save()

        self.instance.reconfigure()

        AkonadiUtils.wait_for_status(self, 0)

    def call_capabilities(self) -> list[str]:
        dbus_proxy = OrgKdeAkonadiImapResourceBaseInterface(
            self._dbus.agent_service_name(self._identifier), "/"
        )
        capabilities = dbus_proxy.server_capabilities()
        return capabilities

    @override
    def remove(self) -> None:
        super().remove()

        with KWalletClient("imap") as kwallet:
            password_exists = kwallet.get_password(self._kwallet_key) is not None
            if password_exists:
                kwallet.remove_password(self._kwallet_key)

    @override
    def resolve_collection(self, collection_name: str) -> Akonadi.Collection:
        path = collection_name.split(self.delimiter)

        def resolve_recursive(parent: Akonadi.Collection, path: list[str]):
            if not path:
                return parent

            collections = self.akonadi_client.list_collections(
                parent_id=parent.id(), first_level=True
            )
            collection = next(
                filter(lambda c: c.name() == path[0] and c.id() != parent.id(), collections), None
            )
            if not collection:
                pytest.fail(f"Collection {collection_name} not found: {path[0]} does not exist!")

            return resolve_recursive(collection, path[1:])

        return resolve_recursive(self.get_root_collection(), path)
