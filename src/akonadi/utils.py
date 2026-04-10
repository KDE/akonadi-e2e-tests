# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
import time

from AkonadiCore import Akonadi  # type: ignore
from PySide6.QtCore import QEventLoop  # type: ignore


class WaitJobError(Exception):
    pass


class AkonadiUtils:
    @staticmethod
    def wait_for_job(job):
        loop = QEventLoop()
        job.result.connect(loop.quit)
        loop.exec()

        if job.error():
            raise WaitJobError(job.errorString())

    # Waits for the resource to go back into given status
    @staticmethod
    async def wait_for_status(identifier, status, timeout: float = 30.0):
        loop = QEventLoop()
        done = False

        def on_status_changed(instance):
            nonlocal done
            if instance.identifier() == identifier and instance.status() == status:
                done = True
                loop.quit()

        manager = Akonadi.AgentManager.self()
        manager.instanceStatusChanged.connect(on_status_changed)

        if manager.instance(identifier).status() == status:
            return

        start = time.time()
        while not done:
            if time.time() - start > timeout:
                raise TimeoutError(f"Resource did not achieve status {status} in time")
            loop.processEvents()
            await asyncio.sleep(0.5)

        manager.instanceStatusChanged.disconnect(on_status_changed)
