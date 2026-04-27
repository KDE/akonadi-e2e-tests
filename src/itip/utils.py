# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from AkonadiCalendar import Akonadi as AkonadiCal  # type: ignore
from PySide6.QtCore import QEventLoop, QTimer  # type: ignore


class ITIPProcessError(Exception):
    pass


class ITIPUtils:
    @staticmethod
    def itip_process_message(
        handler: AkonadiCal.ITIPHandler,
        receiver: str,
        ical: str,
        action: str,
        timeout_ms: int = 30000,
    ):
        loop = QEventLoop()

        timer = QTimer()
        timer.setSingleShot(True)
        timed_out = False

        def on_timeout():
            nonlocal timed_out
            timed_out = True
            # Note it seems we can't stop/kill the itip processing task
            loop.quit()

        error = None

        def on_processed(result, err_msg):
            nonlocal error
            if result != AkonadiCal.ITIPHandler.ResultSuccess:
                is_error = result == AkonadiCal.ITIPHandler.ResultError
                error_type = "Error" if is_error else "Cancelled"
                error = f"{error_type}: {err_msg}"
            timer.stop()
            loop.quit()

        timer.timeout.connect(on_timeout)
        handler.iTipMessageProcessed.connect(on_processed)

        timer.start(timeout_ms)
        handler.processiTIPMessage(receiver, ical, action)
        loop.exec()

        if timed_out:
            raise ITIPProcessError("Timed out while waiting for a job completion")

        if error:
            raise ITIPProcessError(error)
