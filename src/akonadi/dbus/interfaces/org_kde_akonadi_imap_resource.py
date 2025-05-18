# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
)


class OrgKdeAkonadiImapResourceBaseInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.kde.Akonadi.ImapResourceBase",
):
    @dbus_method_async(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="requestManualExpunge",
        result_args_names=(),
    )
    async def request_manual_expunge(
        self,
        collection_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="x",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="configureSubscription",
    )
    async def configure_subscription(
        self,
        window_id: int,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="serverCapabilities",
    )
    async def server_capabilities(
        self,
    ) -> list[str]:
        raise NotImplementedError
