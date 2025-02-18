# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

import asyncio
from datetime import date
from functools import lru_cache, wraps
from typing import Any, Awaitable, Callable, Tuple, TypeVar
from uuid import UUID

from os2mo_helpers.mora_helpers import MoraHelper

from app.config import get_settings


def today() -> date:
    return date.today()


def first_of_month() -> date:
    first_day_of_this_month = today().replace(day=1)
    return first_day_of_this_month


@lru_cache(maxsize=0)
def get_mora_helper(mora_url=None) -> MoraHelper:
    mora_url = mora_url or get_settings().mora_url
    return MoraHelper(hostname=mora_url, use_cache=False)


def get_mora_helper_default() -> MoraHelper:
    return get_mora_helper(None)


CallableReturnType = TypeVar("CallableReturnType")


def async_to_sync(
    func: Callable[..., Awaitable[CallableReturnType]],
) -> Callable[..., CallableReturnType]:
    """Decorator to run an async function to completion.

    Example:

        @async_to_sync
        async def sleepy(seconds):
            await asyncio.sleep(seconds)
            return seconds

        print(sleepy(5))  # --> 5

    Args:
        func (async function): The asynchronous function to wrap.

    Returns:
        :obj:`sync function`: The synchronous function wrapping the async one.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> CallableReturnType:
        return asyncio.run(func(*args, **kwargs))  # type: ignore

    return wrapper


def apply(
    func: Callable[..., CallableReturnType],
) -> Callable[[Tuple], CallableReturnType]:
    """Decorator to apply tuple to function.

    Example:

        @apply
        async def dual(key, value):
            return value

        print(dual(('k', 'v')))  # --> 'v'

    Args:
        func (function): The function to apply arguments for.

    Returns:
        :obj:`sync function`: The function which has had it argument applied.
    """

    @wraps(func)
    def wrapper(tup: Tuple) -> CallableReturnType:
        return func(*tup)

    return wrapper
