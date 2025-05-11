# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Fixtures for Akonadi.

This module contains fixtures for Akonadi. It provides a temporary directory for an
Akonadi instance and a fixture that creates an Akonadi server.
"""

import asyncio
from asyncio.subprocess import Process
from logging import getLogger
import os
from pathlib import Path
import tempfile
from textwrap import dedent
from typing import AsyncGenerator

import pytest

from fixtures.dbus import AkonadiDBus

log = getLogger(__name__)


class AkonadiEnv:
    """Describes the environment for the Akonadi server.

    Returns paths to various configuration files and directories.
    """

    def __init__(self, root_path: Path, instance_id: str) -> None:
        self._root_path = root_path
        self._instance_id = instance_id

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def xdg_config_home(self) -> Path:
        return self._root_path / "config"

    @property
    def xdg_data_home(self) -> Path:
        return self._root_path / "data"

    @property
    def akonadi_config_dir(self) -> Path:
        return self.xdg_config_home / "akonadi/instance" / self._instance_id

    @property
    def akonadi_data_dir(self) -> Path:
        return self.xdg_data_home / "akonadi/instance" / self._instance_id

    @property
    def akonadiserverrc_path(self) -> Path:
        return self.akonadi_config_dir / "akonadiserverrc"

    @property
    def db_path(self) -> Path:
        return self.akonadi_data_dir / "akonadi.db"


class AkonadiServer:
    def __init__(self, instance_id: str, dbus: AkonadiDBus) -> None:
        self._tempdir = Path(os.environ.get("TMPDIR", "/tmp")) / instance_id
        self._instance_id = instance_id
        self._env = AkonadiEnv(self._tempdir, self._instance_id)
        self._dbus = dbus
        self._akonadi_control: Process | None = None

    @property
    def env(self) -> AkonadiEnv:
        return self._env

    async def start(self) -> None:
        """Start the Akonadi server.

        This will start the Akonadi server and wait for it to be ready.

        This manually starts akonadi_control and akonadiserver processes. While it
        would be better to use akonadictl or D-Bus activation to make the tests more
        realistic, it's hard to propagate the environment.
        Maybe if we can eventually run Akonadi in a container, we can use akonadictl,
        because we won't have to bother with isolation from the default Akonadi.
        """
        log.info("Starting Akonadi Server")
        environ = self._prepare_environment()

        self._akonadi_control = await asyncio.create_subprocess_shell(
            "akonadi_control",
            env=environ,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            await self._dbus.wait_for_service(
                self._dbus.akonadi_control_service_name, 10
            )
        except asyncio.TimeoutError:
            stdout, stderr = await self._akonadi_control.communicate()
            log.error("akonadi_control did not start")
            log.error("stdout: %s", stdout)
            log.error("stderr: %s", stderr)
            raise

        await self._dbus.wait_for_service(self._dbus.akonadi_server_service_name, 10)
        log.info("Akonadi Server started")

    async def stop(self) -> None:
        """Stop the Akonadi server.

        This will stop the Akonadi server and wait for it to be stopped.
        """
        log.info("Stopping Akonadi Server")
        if self._akonadi_control is not None:
            control_iface = await self._dbus.control_interface()
            await control_iface.call_shutdown()  # type: ignore

            await self._akonadi_control.wait()
        log.info("Akonadi Server stopped")

    async def is_running(self) -> bool:
        """Check if the Akonadi server is running.

        Returns:
            True if the Akonadi server is running, False otherwise.
        """
        try:
            await self._dbus.wait_for_service(
                self._dbus.akonadi_server_service_name, 0.1
            )
            return True
        except asyncio.TimeoutError:
            return False

    def _prepare_environment(self) -> dict[str, str]:
        """Prepare the environment for the Akonadi server.

        Returns:
            The environment variables to be used for the Akonadi server.
        """

        environ = os.environ.copy()
        environ["HOME"] = str(self._tempdir / "home")
        environ["TMPDIR"] = str(self._tempdir / "tmp")
        environ["XDG_CONFIG_HOME"] = str(self._tempdir / "config")
        environ["XDG_CACHE_HOME"] = str(self._tempdir / "cache")
        environ["XDG_DATA_HOME"] = str(self._tempdir / "data")
        environ["AKONADI_INSTANCE"] = self._instance_id
        environ["AKONADI_DISABLE_AGENT_AUTOSTART"] = "true"

        os.makedirs(self._env.akonadi_config_dir, exist_ok=True)
        os.makedirs(self._env.akonadi_data_dir, exist_ok=True)

        self._write_server_config()
        self._write_first_run_config()

        return environ

    def _write_server_config(self) -> None:
        with open(self._env.akonadiserverrc_path, "w", encoding="utf-8") as f:
            f.write(
                dedent(f"""
                [Debug]
                Tracer = null

                [%General]
                Driver=QSQLITE

                [QSQLITE]
                Name={self._env.db_path}
            """)
            )

    def _write_first_run_config(self) -> None:
        with open(
            self._env.xdg_config_home / "akonadi-firstrunc", "w", encoding="utf-8"
        ) as f:
            f.write(
                dedent("""
                [ProcessedDefaults]
                defaultaddressbook=done
                defaultcalendar=done
                defaultnotebook=done
            """)
            )


@pytest.fixture()
async def instance_id() -> AsyncGenerator[str, None]:
    """Pytest fixture that creates a temporary directory for an Akonadi instance.

    Returns:
        The instance ID of the Akonadi instance.
    """
    with tempfile.TemporaryDirectory(prefix="akonadi-e2e-", delete=False) as tempdir:
        yield Path(tempdir).name


@pytest.fixture()
async def akonadi_server(
    instance_id: str, dbus_client: AkonadiDBus
) -> AsyncGenerator[AkonadiServer, None]:
    """Pytest fixture that creates an Akonadi server.

    Returns:
        The Akonadi server.
    """

    server = AkonadiServer(instance_id, dbus_client)
    await server.start()
    yield server
    await server.stop()
