# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
import grp
from logging import getLogger
import os
from pathlib import Path
from textwrap import dedent

log = getLogger(__name__)


class CyrusServer:
    def __init__(self, root_dir: Path):
        self._server = None
        self._root_dir = root_dir

    @property
    def port(self) -> int:
        # TODO: Randomize this
        return 9993

    async def start(self):
        log.info("Starting Cyrus-IMAP server")
        os.makedirs(Path(f"/tmp/{self._root_dir}/cyrus/etc"), exist_ok=True)
        os.makedirs(Path(f"/tmp/{self._root_dir}/cyrus/log"), exist_ok=True)
        os.makedirs(Path(f"/tmp/{self._root_dir}/cyrus/run"), exist_ok=True)
        imapd_conf_path = self._write_imapd_conf()
        cyrus_conf_path = self._write_cyrus_conf(imapd_conf_path)
        log_path = Path(f"/tmp/{self._root_dir}/cyrus/log/cyrus.log")

        self._server = await asyncio.create_subprocess_exec(
            "/usr/lib/cyrus/master",
            *["-C", imapd_conf_path, "-M", cyrus_conf_path, "-L", log_path],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            await asyncio.wait_for(self._try_connect(), timeout=10.0)
        except asyncio.TimeoutError:
            log.error(
                "Timeout while waiting for Cyrus-IMAP server to start accepting connections"
            )
            self._server.kill()
            raise

        log.info("Cyrus-IMAP server started")

    async def stop(self):
        log.info("Stopping Cyrus-IMAP server")
        self._server.terminate()
        try:
            await asyncio.wait_for(self._server.wait(), timeout=10)
        except asyncio.TimeoutError:
            log.warning("Cyrus-IMAP server did not terminate in time, killing it")
            self._server.kill()

        log.info("Cyrus-IMAP server stopped")

    def _write_imapd_conf(self) -> Path:
        base_dir = Path(f"/tmp/{self._root_dir}/cyrus/")
        imapd_conf_path = Path(f"{base_dir}/etc/imapd.conf")
        with open(imapd_conf_path, "w", encoding="utf-8") as f:
            f.write(
                dedent(f"""
            # This is the most minimal Cyrus config ever - it stores everything into /tmp/<instance_id>/cyrus
            # and accepts any credentials for login.

            # Root where cyrus will store everything
            configdirectory: {base_dir}/conf
            master_pid_file: {base_dir}/run/master.pid

            # This probably must be set
            defaultpartition: default
            partition-default: {base_dir}/var/spool/mail
            # This must be set, defaults to /usr/lib otherwise
            sievedir: {base_dir}/var/spool/sieve

            cyrus_user: {os.getlogin()}
            cyrus_group: {grp.getgrgid(os.getgid()).gr_name}

            # Allow plaintext login yes, please
            allowplaintext: yes
            # Whatever the credentials are, they are accepted - we don't want to bother with setting
            # up users for our tests, so we just accept any and all credentials.
            sasl_pwcheck_method: alwaystrue
            """)
            )
        return imapd_conf_path

    def _write_cyrus_conf(self, imapd_conf_path: Path) -> Path:
        cyrus_conf_path = Path(f"/tmp/{self._root_dir}/cyrus/etc/cyrus.conf")
        with open(cyrus_conf_path, "w", encoding="utf-8") as f:
            f.write(
                dedent(f"""
            START {{
                recover       cmd="ctl_cyrusdb -r -C {imapd_conf_path}"
            }}

            SERVICES {{
                imap          cmd="imapd -C {imapd_conf_path}" listen="9993" prefork=0
            }}

            EVENTS {{
                checkpoint    cmd="ctl_cyrusdb -c -C {imapd_conf_path}" period=30
            }}
            """)
            )
        return cyrus_conf_path

    async def _try_connect(self):
        """This is kinda stupid, but we need to make sure the server is ready to accept
        connections, othwerise the tests may get stuck.
        """
        while True:
            try:
                await asyncio.wait_for(
                    asyncio.open_connection(host="127.0.0.1", port=self.port),
                    timeout=0.5,
                )
                return
            except asyncio.TimeoutError:
                await asyncio.sleep(0.1)
            except OSError:
                await asyncio.sleep(0.1)
