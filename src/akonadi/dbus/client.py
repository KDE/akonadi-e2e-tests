import asyncio
from logging import getLogger
from sdbus import SdBus, sd_bus_open
from sdbus.exceptions import DbusNameHasNoOwnerError
from sdbus_async.dbus_daemon import FreedesktopDbus

from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_agent_control import (
    OrgFreedesktopAkonadiAgentControlInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_controlmanager import (
    OrgFreedesktopAkonadiControlManagerInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_resource import (
    OrgFreedesktopAkonadiResourceInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_server import (
    OrgFreedesktopAkonadiServerInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_agent_manager import (
    OrgFreedesktopAkonadiAgentManagerInterface,
)

log = getLogger(__name__)


class AkonadiDBus:
    """A high-level client for the Akonadi DBus service."""

    def __init__(self, instance_id: str) -> None:
        self._instance_id = instance_id
        self._client = sd_bus_open()

    def close(self) -> None:
        self._client.close()

    async def wait_for_service(
        self, service_name: str, timeout_secs: float = 10
    ) -> None:
        await asyncio.wait_for(
            self._wait_for_name_owner(service_name),
            timeout=timeout_secs,
        )

    @property
    def client(self) -> SdBus:
        return self._client

    @property
    def akonadi_server_service_name(self) -> str:
        return f"org.freedesktop.Akonadi.{self._instance_id}"

    @property
    def akonadi_control_service_name(self) -> str:
        return f"org.freedesktop.Akonadi.Control.{self._instance_id}"

    def resource_service_name(self, instance_id: str) -> str:
        return f"org.freedesktop.Akonadi.Resource.{instance_id}.{self._instance_id}"

    def agent_service_name(self, instance_id: str) -> str:
        return f"org.freedesktop.Akonadi.Agent.{instance_id}.{self._instance_id}"

    @property
    def control_interface(self) -> OrgFreedesktopAkonadiControlManagerInterface:
        return OrgFreedesktopAkonadiControlManagerInterface.new_proxy(
            self.akonadi_control_service_name,
            "/ControlManager",
            self._client,
        )

    @property
    def server_interface(self) -> OrgFreedesktopAkonadiServerInterface:
        return OrgFreedesktopAkonadiServerInterface.new_proxy(
            self.akonadi_server_service_name,
            "/Server",
            self._client,
        )

    @property
    def agent_manager_interface(self) -> OrgFreedesktopAkonadiAgentManagerInterface:
        return OrgFreedesktopAkonadiAgentManagerInterface.new_proxy(
            self.akonadi_control_service_name,
            "/AgentManager",
            self._client,
        )

    def agent_interface(
        self, instance_name: str
    ) -> OrgFreedesktopAkonadiAgentControlInterface:
        return OrgFreedesktopAkonadiAgentControlInterface.new_proxy(
            self.agent_service_name(instance_name),
            "/",
            self._client,
        )

    def resource_interface(
        self, instance_name: str
    ) -> OrgFreedesktopAkonadiResourceInterface:
        return OrgFreedesktopAkonadiResourceInterface.new_proxy(
            self.resource_service_name(instance_name),
            "/",
            self._client,
        )

    async def _wait_for_name_owner(self, service_name: str) -> None:
        log.debug("Waiting for name owner of %s", service_name)
        dbus = FreedesktopDbus.new_proxy(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            self._client,
        )

        async def name_owner_changed() -> None:
            async for name, _, new_owner in dbus.name_owner_changed.catch():
                if name == service_name:
                    log.debug("Name owner changed: %s -> %s", name, new_owner)
                    return

        try:
            resp = await dbus.get_name_owner(service_name)
        except DbusNameHasNoOwnerError:
            log.debug("Service %s has no owner, waiting for it...", service_name)
            await asyncio.wait_for(name_owner_changed(), timeout=10)
        else:
            log.debug("Service %s has owner %s, continuing", service_name, resp)
