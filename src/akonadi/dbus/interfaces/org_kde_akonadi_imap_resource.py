# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgKdeAkonadiImapResourceBaseInterface(
    DbusInterfaceCommon,
    interface_name="org.kde.Akonadi.ImapResourceBase",
):
    @dbus_method(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="requestManualExpunge",
    )
    def request_manual_expunge(
        self,
        collection_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="x",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="configureSubscription",
    )
    def configure_subscription(
        self,
        window_id: int,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="serverCapabilities",
    )
    def server_capabilities(
        self,
    ) -> list[str]:
        raise NotImplementedError
