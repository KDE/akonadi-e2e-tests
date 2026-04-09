# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from collections.abc import Callable, Coroutine
from time import time
from typing import Any


async def wait_until(
    condition: Callable[[], bool] | Callable[[], Coroutine[Any, Any, bool]],
    timeout: float = 5.0,
    interval: float = 0.2,
) -> None:
    """Checks the condition until it returns True or the timeout is reached.

    If the condition is not met before the timeout expires, an assertion is raised.
    """
    start = time()

    while True:
        result = condition()

        if asyncio.iscoroutine(result):
            result = await result

        if result:
            return

        if time() - start > timeout:
            result = condition()
            if asyncio.iscoroutine(result):
                result = await result
            assert result, f"Condition not met within {timeout} seconds"

        await asyncio.sleep(interval)
