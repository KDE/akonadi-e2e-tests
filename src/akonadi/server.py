# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
import os
from asyncio.streams import StreamReader
from asyncio.subprocess import Process
from logging import getLogger
from pathlib import Path
from textwrap import dedent

from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.env import AkonadiEnv

log = getLogger(__name__)


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

        async def read_stdout(stream: StreamReader | None) -> None:
            while stream is not None:
                line = await stream.readline()
                if line:
                    log.debug("akonadi_control: %s", line.decode().strip())
                else:
                    log.debug("akonadi_control stdout closed")
                    break

        self._akonadi_control_reader = asyncio.create_task(
            read_stdout(self._akonadi_control.stderr)
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
            await self._dbus.control_interface.shutdown()

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
        environ = self._env.environ
        environ["AKONADI_DISABLE_AGENT_AUTOSTART"] = "true"
        environ["QT_LOGGING_RULES"] = "*.debug=true;qt.*.debug=false"

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
