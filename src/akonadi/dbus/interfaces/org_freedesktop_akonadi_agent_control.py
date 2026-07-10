# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgFreedesktopAkonadiAgentControlInterface(
    DbusInterfaceCommon,
    interface_name="org.freedesktop.Akonadi.Agent.Control",
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
        flags=DbusUnprivilegedFlag,
        method_name="cleanup",
    )
    def cleanup(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="configure",
    )
    def configure(
        self,
        window_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="reconfigure",
    )
    def reconfigure(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="abort",
    )
    def abort(
        self,
    ) -> None:
        raise NotImplementedError
