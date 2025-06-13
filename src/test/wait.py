# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from inspect import iscoroutinefunction
from time import time
from typing import Any, Callable, Coroutine, cast


async def wait_until(
    condition: Callable[[], bool] | Callable[[], Coroutine[Any, Any, bool]],
    timeout: float = 5.0,
    interval: float = 0.2,
) -> None:
    """Checks the condition until it returns True or the timeout is reached.

    If the condition is not met before the timeout expires, an assertion is raised.
    """

    async def check_condition() -> bool:
        if iscoroutinefunction(condition):
            return await condition()
        else:
            return cast(bool, condition())

    start = time()

    while True:
        if await check_condition():
            return

        if time() - start > timeout:
            assert await check_condition(), (
                f"Condition not met within {timeout} seconds"
            )

        await asyncio.sleep(interval)
