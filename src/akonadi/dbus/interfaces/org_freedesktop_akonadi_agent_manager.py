# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from typing import Any

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
    dbus_signal_async,
)


class OrgFreedesktopAkonadiAgentManagerInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.freedesktop.Akonadi.AgentManager",
):
    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentTypes",
    )
    async def agent_types(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentName",
    )
    async def agent_name(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentComment",
    )
    async def agent_comment(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentIcon",
    )
    async def agent_icon(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentMimeTypes",
    )
    async def agent_mime_types(
        self,
        identifier: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentCapabilities",
    )
    async def agent_capabilities(
        self,
        identifier: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="agentCustomProperties",
    )
    async def agent_custom_properties(
        self,
        identifier: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="createAgentInstance",
    )
    async def create_agent_instance(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="removeAgentInstance",
        result_args_names=(),
    )
    async def remove_agent_instance(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceType",
    )
    async def agent_instance_type(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstances",
    )
    async def agent_instances(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceStatus",
    )
    async def agent_instance_status(
        self,
        identifier: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceStatusMessage",
    )
    async def agent_instance_status_message(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="u",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceProgress",
    )
    async def agent_instance_progress(
        self,
        identifier: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceProgressMessage",
    )
    async def agent_instance_progress_message(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="ss",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceName",
        result_args_names=(),
    )
    async def set_agent_instance_name(
        self,
        identifier: str,
        name: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceName",
    )
    async def agent_instance_name(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sx",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceConfigure",
        result_args_names=(),
    )
    async def agent_instance_configure(
        self,
        identifier: str,
        window_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronize",
        result_args_names=(),
    )
    async def agent_instance_synchronize(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronizeCollectionTree",
        result_args_names=(),
    )
    async def agent_instance_synchronize_collection_tree(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sxb",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronizeCollection",
        result_args_names=(),
    )
    async def agent_instance_synchronize_collection(
        self,
        identifier: str,
        collection: int,
        recursive: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronizeTags",
        result_args_names=(),
    )
    async def agent_instance_synchronize_tags(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceOnline",
    )
    async def agent_instance_online(
        self,
        identifier: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sb",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceOnline",
        result_args_names=(),
    )
    async def set_agent_instance_online(
        self,
        identifier: str,
        state: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceActivities",
    )
    async def agent_instance_activities(
        self,
        identifier: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sas",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceActivities",
        result_args_names=(),
    )
    async def set_agent_instance_activities(
        self,
        identifier: str,
        activities: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="restartAgentInstance",
        result_args_names=(),
    )
    async def restart_agent_instance(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sb",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceActivitiesEnabled",
        result_args_names=(),
    )
    async def set_agent_instance_activities_enabled(
        self,
        identifier: str,
        en: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceActivitiesEnabled",
    )
    async def agent_instance_activities_enabled(
        self,
        identifier: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=("agentType",),
        signal_name="typeAdded",
    )
    def agent_type_added(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=("agentType",),
        signal_name="typeRemoved",
    )
    def agent_type_removed(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=("agentIdentifier",),
        signal_name="instanceAdded",
    )
    def agent_instance_added(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=("agentIdentifier",),
        signal_name="instanceRemoved",
    )
    def agent_instance_removed(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="sis",
        signal_args_names=("agentIdentifier", "status", "message"),
        signal_name="statusChanged",
    )
    def agent_instance_status_changed(self) -> tuple[str, int, str]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="sa{sv}",
        signal_args_names=("agentIdentifier", "status"),
        signal_name="advancedStatusChanged",
    )
    def agent_instance_advanced_status_changed(
        self,
    ) -> tuple[str, dict[str, tuple[str, Any]]]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="sus",
        signal_args_names=("agentIdentifier", "progress", "message"),
        signal_name="progressChanged",
    )
    def agent_instance_progress_changed(self) -> tuple[str, int, str]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="ss",
        signal_args_names=("agentIdentifier", "name"),
        signal_name="nameChanged",
    )
    def agent_instance_name_changed(self) -> tuple[str, str]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="ss",
        signal_args_names=("agentIdentifier", "message"),
        signal_name="warning",
    )
    def agent_instance_warning(self) -> tuple[str, str]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="ss",
        signal_args_names=("agentIdentifier", "message"),
        signal_name="error",
    )
    def agent_instance_error(self) -> tuple[str, str]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="sb",
        signal_args_names=("agentIdentifier", "state"),
        signal_name="onlineChanged",
    )
    def agent_instance_online_changed(self) -> tuple[str, bool]:
        raise NotImplementedError
