# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
    dbus_signal_async,
)


class OrgFreedesktopAkonadiResourceInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.freedesktop.Akonadi.Resource",
):
    @dbus_method_async(
        input_signature="axaay",
        flags=DbusUnprivilegedFlag,
        method_name="requestItemDelivery",
        result_args_names=(),
    )
    async def request_item_delivery(
        self,
        uids: list[int],
        parts: list[bytes],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="synchronize",
        result_args_names=(),
    )
    async def synchronize(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeCollectionTree",
        result_args_names=(),
    )
    async def synchronize_collection_tree(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="xb",
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeCollection",
        result_args_names=(),
    )
    async def synchronize_collection(
        self,
        collection_id: int,
        recursive: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeCollectionAttributes",
        result_args_names=(),
    )
    async def synchronize_collection_attributes(
        self,
        collection_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeTags",
        result_args_names=(),
    )
    async def synchronize_tags(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setName",
        result_args_names=(),
    )
    async def set_name(
        self,
        name: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="name",
    )
    async def name(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setActivities",
        result_args_names=(),
    )
    async def set_activities(
        self,
        name: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="activities",
    )
    async def activities(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setActivitiesEnabled",
        result_args_names=(),
    )
    async def set_activities_enabled(
        self,
        en: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="activitiesEnabled",
    )
    async def activities_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=("name",),
        signal_name="nameChanged",
    )
    def name_changed(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_args_names=(),
        signal_name="synchronized",
    )
    def synchronized(self) -> None:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="x",
        signal_args_names=("collectionId",),
        signal_name="attributesSynchronized",
    )
    def attributes_synchronized(self) -> int:
        raise NotImplementedError

    @dbus_signal_async(
        signal_args_names=(),
        signal_name="collectionTreeSynchronized",
    )
    def collection_tree_synchronized(self) -> None:
        raise NotImplementedError
