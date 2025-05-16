from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
)


class OrgFreedesktopAkonadiServerInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.freedesktop.Akonadi.Server",
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
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="serverPath",
        result_args_names=("path",),
    )
    async def server_path(
        self,
    ) -> str:
        raise NotImplementedError
