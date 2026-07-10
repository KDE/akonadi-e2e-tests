# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgFreedesktopAkonadiServerInterface(
    DbusInterfaceCommon,
    interface_name="org.freedesktop.Akonadi.Server",
):
    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="quit",
    )
    def quit(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="serverPath",
    )
    def server_path(
        self,
    ) -> str:
        raise NotImplementedError
