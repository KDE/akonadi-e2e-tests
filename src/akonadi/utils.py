# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import time

from AkonadiCore import Akonadi  # type: ignore
from PySide6.QtCore import QEventLoop, QTimer  # type: ignore


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
    def wait_for_status(identifier, status, timeout: float = 30.0):
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
            time.sleep(0.2)

        manager.instanceStatusChanged.disconnect(on_status_changed)

    # Waits until an instanceOnline signal with the given agent identifier and online state is caught
    @staticmethod
    def wait_for_online(identifier, online, timeout_ms: int = 30000):
        loop = QEventLoop()

        timer = QTimer()
        timer.setSingleShot(True)

        timed_out = False

        manager = Akonadi.AgentManager.self()

        def on_timeout():
            nonlocal timed_out
            timed_out = True
            manager.instanceOnline.disconnect(on_online_changed)
            loop.quit()

        def on_online_changed(instance):
            if instance.identifier() == identifier and instance.isOnline() == online:
                manager.instanceOnline.disconnect(on_online_changed)
                timer.stop()
                loop.quit()

        timer.timeout.connect(on_timeout)
        manager.instanceOnline.connect(on_online_changed)

        timer.start(timeout_ms)
        loop.exec()

        if timed_out:
            raise WaitJobError(
                f"Timed out while waiting for online state {online} of agent {identifier}"
            )
