# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
)


class OrgFreedesktopAkonadiControlManagerInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.freedesktop.Akonadi.ControlManager",
):
    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="shutdown",
        result_args_names=(),
    )
    async def shutdown(
        self,
    ) -> None:
        raise NotImplementedError
