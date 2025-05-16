from src.akonadi.dbus.client import AkonadiDBus


class ImapResource:
    RESOURCE_TYPE = "akonadi_imap_resource"

    def __init__(self, dbus: AkonadiDBus, instance_id: str) -> None:
        self._dbus = dbus
        self._instance_id = instance_id

    @classmethod
    async def create(cls, dbus: AkonadiDBus) -> "ImapResource":
        instance_id = await dbus.agent_manager_interface.create_agent_instance(
            cls.RESOURCE_TYPE
        )

        return ImapResource(dbus, instance_id)

    @property
    def instance_id(self) -> str:
        return self._instance_id
