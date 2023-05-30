import sqlite3
from io import StringIO
from datetime import datetime

from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton
)


from ..settings import Settings


form_router: Dispatcher = Settings.Dispatcher
MainForm: StatesGroup = Settings.Form


@form_router.message(
    MainForm.main,
    F.text.casefold() == 'просмотреть напоминания'
)
async def view_reminders(message: Message, state: FSMContext) -> None:
    db = Settings.Database
    with db.cursor() as cur:
        cur: sqlite3.Cursor
        reminders = cur.execute(
            "SELECT datetime, text "
            "FROM reminds "
            f"WHERE OWNER=? "
            "ORDER BY datetime DESC",
            (message.from_user.id,)
        ).fetchmany(5)
    output = StringIO()
    amount = len(reminders)
    if amount == 0:
        output.write('У вас нет напоминаний')
    elif amount == 1:
        output.write('Ваше одно напоминание:')
    elif amount < 5:
        output.write(f'Ваши {amount} напоминания:')
    else:
        output.write('Ваши 5 напоминаний:')

    for (date, text) in reminders:
        text: str
        date: int
        date: datetime = datetime.fromtimestamp(date, Settings.timezone)
        output.write(f'\n\n> Напоминание на {date:%d.%m.%y %H:%M}:\n')
        if len(text) > 50:
            last_space = text.find(' ', 50, 100)
            last_new_line = text.find('\n', 50, 100)
            last_character = min(last_space, last_new_line)
            output.write(text[:last_character])
            output.write(' ...')
        else:
            output.write(text)

    await message.answer(output.getvalue())
    await Settings.main_menu(message=message, state=state)
