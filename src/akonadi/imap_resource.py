# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later


from logging import getLogger

from sdbus import DbusInterfaceCommonAsync, DbusUnprivilegedFlag, dbus_method_async

from src.akonadi.dbus.interfaces.org_kde_akonadi_imap_settings import (
    OrgKdeAkonadiImapSettingsInterface,
)
from src.akonadi.resource import Resource

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


class ImapResource(Resource):
    RESOURCE_TYPE = "akonadi_imap_resource"

    async def configure(
        self, host: str, port: int, username: str, password: str
    ) -> None:
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

        # Force-reload the config
        await self._dbus.agent_interface(self._identifier).reconfigure()
