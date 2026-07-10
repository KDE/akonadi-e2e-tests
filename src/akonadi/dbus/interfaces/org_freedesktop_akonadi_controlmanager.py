# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgFreedesktopAkonadiControlManagerInterface(
    DbusInterfaceCommon,
    interface_name="org.freedesktop.Akonadi.ControlManager",
):
    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="shutdown",
    )
    def shutdown(
        self,
    ) -> None:
        raise NotImplementedError
