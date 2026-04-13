# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import time
from logging import getLogger
from textwrap import dedent

from AkonadiCore import Akonadi  # type: ignore

from src.akonadi.env import AkonadiEnv

log = getLogger(__name__)


class AkonadiServer:
    def __init__(self, akonadi_env: AkonadiEnv) -> None:
        self._env = akonadi_env

    @property
    def env(self) -> AkonadiEnv:
        return self._env

    def start(self) -> None:
        """Start the Akonadi server.

        This will start the Akonadi server.
        """
        log.info("Starting Akonadi Server")
        self._prepare_environment()

        Akonadi.Control.start()

        for _ in range(50):
            if Akonadi.ServerManager.isRunning():
                log.info("Akonadi Server started")
                return
            time.sleep(0.1)

        raise RuntimeError("Akonadi server failed to start in time")

    def stop(self) -> None:
        """Stop the Akonadi server.

        This will stop the Akonadi server.
        """
        log.info("Stopping Akonadi Server")
        Akonadi.Control.stop()
        log.info("Akonadi Server stopped")

    def is_running(self) -> bool:
        """Check if the Akonadi server is running.

        Returns:
            True if the Akonadi server is running, False otherwise.
        """
        return Akonadi.ServerManager.isRunning()

    def akonadiconsole_command(self) -> str:
        """Get the command to launch akonadiconsole for debugging purposes."""
        return f"XDG_CONFIG_HOME={self._env.xdg_config_home} XDG_DATA_HOME={self._env.xdg_data_home} XDG_CACHE_HOME={self._env.xdg_cache_home} HOME={self._env.home_dir} AKONADI_INSTANCE={self._env.instance_id} akonadiconsole"

    def _prepare_environment(self) -> None:
        """Prepare the environment for the Akonadi server."""

        os.makedirs(self._env.akonadi_config_dir, exist_ok=True)
        os.makedirs(self._env.akonadi_data_dir, exist_ok=True)

        self._write_server_config()
        self._write_first_run_config()

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
        with open(self._env.xdg_config_home / "akonadi-firstrunc", "w", encoding="utf-8") as f:
            f.write(
                dedent("""
                [ProcessedDefaults]
                defaultaddressbook=done
                defaultcalendar=done
                defaultnotebook=done
            """)
            )
