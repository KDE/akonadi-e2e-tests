# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from AkonadiCore import Akonadi  # type: ignore
from PySide6.QtCore import QEventLoop, QTimer  # type: ignore


class WaitJobError(Exception):
    pass


class AkonadiUtils:
    @staticmethod
    def wait_for_job(job, timeout_ms: int = 30000):
        loop = QEventLoop()

        timer = QTimer()
        timer.setSingleShot(True)

        timed_out = False

        def on_timeout():
            nonlocal timed_out
            timed_out = True
            job.kill()
            loop.quit()

        def on_job_finished():
            timer.stop()
            loop.quit()

        timer.timeout.connect(on_timeout)
        job.result.connect(on_job_finished)

        timer.start(timeout_ms)
        loop.exec()

        if timed_out:
            raise WaitJobError("Timed out while waiting for a job completion")

        if job.error():
            raise WaitJobError(job.errorString())

    # Waits for the resource to go back into given status
    @staticmethod
    def wait_for_status(identifier, status, timeout_ms: int = 30000):
        loop = QEventLoop()

        timer = QTimer()
        timer.setSingleShot(True)

        timed_out = False

        manager = Akonadi.AgentManager.self()

        def on_timeout():
            nonlocal timed_out
            timed_out = True
            manager.instanceStatusChanged.disconnect(on_status_changed)
            loop.quit()

        def on_status_changed(instance):
            if instance.identifier() == identifier and instance.status() == status:
                manager.instanceStatusChanged.disconnect(on_status_changed)
                timer.stop()
                loop.quit()

        timer.timeout.connect(on_timeout)
        manager.instanceStatusChanged.connect(on_status_changed)

        timer.start(timeout_ms)
        loop.exec()

        if timed_out:
            raise WaitJobError(f"Timed out while waiting for status {status}")

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
