import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.utils.token import TokenValidationError

from .settings import Settings


async def main(token: str) -> None:
    """Main running function. Creates bot, dispatcher and starts polling"""
    Settings['Bot'] = Bot(token=token)
    Settings['Dispatcher'] = Dispatcher()
    from . import states_functions
    await Settings['Dispatcher'].start_polling(Settings['Bot'])


def run() -> None:
    """Cli-function to run app with one-line call"""
    args = sys.argv[1:]
    if len(args) < 1:
        raise RuntimeError('To run server, pass token as first argument')
    token = args[0]
    try:
        loop = asyncio.new_event_loop()
        Settings.loop = loop
        loop.run_until_complete(main(token))
    except TokenValidationError as e:
        raise TokenValidationError('Token is invalid') from e
