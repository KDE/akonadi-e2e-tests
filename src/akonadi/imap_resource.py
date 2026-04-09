# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override

from AkonadiCore import Akonadi  # type: ignore
from sdbus import DbusInterfaceCommonAsync, DbusUnprivilegedFlag, dbus_method_async

from src.akonadi.client import AkonadiClient
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.dbus.interfaces.org_kde_akonadi_imap_settings import (
    OrgKdeAkonadiImapSettingsInterface,
)
from src.akonadi.resource import Resource
from src.kwallet.client import KWalletClient

log = getLogger(__name__)


class WalletIface(DbusInterfaceCommonAsync, interface_name="org.kde.Akonadi.Imap.Wallet"):
    @dbus_method_async(
        input_signature="s",
        result_signature="",
        result_args_names="password",
        flags=DbusUnprivilegedFlag,
        method_name="setPassword",
    )
    async def set_password(self, password: str) -> None:
        pass


class ImapResource(Resource):
    RESOURCE_TYPE = "akonadi_imap_resource"

    def __init__(self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, identifier: str) -> None:
        super().__init__(akonadi_client, dbus, identifier)
        self._kwallet_key = f"{self._identifier}_{self.akonadi_client.akonadi_instance_name}rc"

    async def configure(self, host: str, port: int, username: str, password: str) -> None:
        settings = OrgKdeAkonadiImapSettingsInterface.new_proxy(
            self._dbus.resource_service_name(self._identifier),
            "/Settings",
            self._dbus.client,
        )

        await settings.set_imap_server(host)
        await settings.set_imap_port(port)
        await settings.set_safety("PLAIN")
        await settings.set_authentication(1)
        await settings.set_user_name(username)

        wallet = WalletIface.new_proxy(
            self._dbus.resource_service_name(self._identifier),
            "/Settings",
            self._dbus.client,
        )
        await wallet.set_password(password)

        await settings.save()

        instance = Akonadi.AgentManager.self().instance(self._identifier)
        instance.reconfigure()

        await self.wait_for_status(0)

    @override
    async def remove(self) -> None:
        await super().remove()

        async with KWalletClient("imap") as kwallet:
            password_exists = await kwallet.get_password(self._kwallet_key) is not None
            if password_exists:
                await kwallet.remove_password(self._kwallet_key)
