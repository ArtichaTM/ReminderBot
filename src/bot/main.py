import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.utils.token import TokenValidationError
from datetime import timezone, timedelta, datetime

from .settings import Settings
from .db import Database
from .paths import DB_REMINDS
from .reminders_cycle import start_cycle


async def user_notify() -> None:
    current_time: float = datetime.now(Settings.timezone).timestamp()
    bot: Bot = Settings.Bot
    with Settings.Database.cursor(autocommit=True) as cur:
        reminders = cur.execute(
            'SELECT rowid, datetime, owner, text '
            "FROM 'reminds' "
            f"WHERE datetime < {int(current_time)}"
        ).fetchall()

        if not reminders:
            return

        cur.execute(
            "DELETE FROM 'reminds' "
            f"WHERE datetime < {int(current_time)}"
        )

    for reminder in reminders:
        asyncio.create_task(bot.send_message(reminder[2], reminder[3]))


async def main(token: str) -> None:
    """Main running function. Creates bot, dispatcher and starts polling"""
    Settings.timezone = timezone(timedelta(hours=3), name='MSK')
    Settings.Bot = Bot(token=token)
    Settings.Dispatcher = Dispatcher()
    Settings.Database = Database(DB_REMINDS.absolute())
    from . import states_functions
    start_cycle()
    Settings.minute_notify_list.append(user_notify)
    try:
        await Settings.Dispatcher.start_polling(Settings.Bot)
    finally:
        # Unload instances
        await Settings.Database.unload_instance()


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
