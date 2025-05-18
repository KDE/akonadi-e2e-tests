# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
    dbus_signal_async,
)


class OrgFreedesktopAkonadiAgentControlInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.freedesktop.Akonadi.Agent.Control",
):
    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="quit",
        result_args_names=(),
    )
    async def quit(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="cleanup",
        result_args_names=(),
    )
    async def cleanup(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="configure",
        result_args_names=(),
    )
    async def configure(
        self,
        window_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="reconfigure",
        result_args_names=(),
    )
    async def reconfigure(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="abort",
        result_args_names=(),
    )
    async def abort(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_signal_async(
        signal_args_names=(),
        signal_name="configurationDialogAccepted",
    )
    def configuration_dialog_accepted(self) -> None:
        raise NotImplementedError

    @dbus_signal_async(
        signal_args_names=(),
        signal_name="configurationDialogRejected",
    )
    def configuration_dialog_rejected(self) -> None:
        raise NotImplementedError
