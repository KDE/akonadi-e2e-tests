# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from collections.abc import Callable, Coroutine
from time import sleep, time
from typing import Any

from PySide6.QtCore import QCoreApplication


def wait_until(
    condition: Callable[[], bool] | Callable[[], Coroutine[Any, Any, bool]],
    timeout: float = 5.0,
    interval: float = 0.2,
) -> None:
    """Checks the condition until it returns True or the timeout is reached.

    If the condition is not met before the timeout expires, an assertion is raised.
    """
    start = time()

    while True:
        QCoreApplication.processEvents()
        result = condition()

        if result:
            return

        if time() - start > timeout:
            result = condition()
            assert result, f"Condition not met within {timeout} seconds"

        sleep(interval)
