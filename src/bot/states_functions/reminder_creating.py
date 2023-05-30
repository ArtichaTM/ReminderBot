from datetime import datetime, timedelta
from typing import Optional, List

from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton
)

from ..settings import Settings
from .states_class import Form


form_router: Dispatcher = Settings.Dispatcher


class NewReminderStates(StatesGroup):
    main = State()

    new_date = State()
    new_interval = State()

    text_date = State()
    text_interval = State()


@form_router.message(
    Form.main,
    F.text.casefold() == 'создать напоминание'
)
async def new_reminder(message: Message, state: FSMContext) -> None:
    await message.answer(
        'Каким образом задать время напоминания?',
        reply_markup=ReplyKeyboardMarkup(keyboard=[[
            KeyboardButton(text='Дата и время'),
            # KeyboardButton(text='Интервал'),
        ]], resize_keyboard=True)
    )
    await state.set_state(NewReminderStates.main)


@form_router.message(
    NewReminderStates.main,
    F.text.casefold() == 'дата и время'
)
async def new_date(message: Message, state: FSMContext) -> None:
    current_date = datetime.now(Settings.timezone)
    await message.answer(
        'Введите дату в формате ДД.ММ.ГГ ЧЧ:ММ, где:\n'
        '• Д - номер дня месяца\n'
        '• М - номер месяца\n'
        '• Г - номер года\n'
        '• Ч - час напоминания\n'
        '• М - минута напоминания\n'
        'Дата обязательно, время необязательно. В случае '
        'отсутствия времени устанавливается текущее.\n'
        f'Текущая дата и время (MSK): {current_date:%d.%m.%y %H:%M}',
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(NewReminderStates.new_date)


@form_router.message(
    NewReminderStates.main,
    F.text.casefold() == 'интервал'
)
async def new_interval(message: Message, state: FSMContext) -> None:
    await message.answer(
        'Введите дату в формате ДД.ММ.ГГ ЧЧ:ММ, где:\n',
        reply_markup=ReplyKeyboardMarkup(keyboard=[[
            KeyboardButton(text='Coci'),
        ]], resize_keyboard=True)
    )
    await state.set_state(NewReminderStates.new_interval)


async def analyze_date(message: Message) -> Optional[datetime | List[str]]:
    answer: List[str] = []
    current = datetime.now(Settings.timezone)
    text = message.text
    try:
        day = int(text[0:2])
    except ValueError:
        await message.answer(f'Не смог прочитать день напоминания: "{text[0:2]}"')
        return
    try:
        month = int(text[3:5])
    except ValueError:
        await message.answer(f'Не смог прочитать месяц напоминания: "{text[3:5]}"')
        return
    try:
        year = int(text[6:8])
    except ValueError:
        await message.answer(f'Не смог прочитать год напоминания: "{text[6:8]}"')
        return

    hour = text[9:11]
    if hour:
        try:
            hour = int(hour)
        except ValueError:
            await message.answer(f'Не смог прочитать час напоминания: "{hour}"')
            return
        try:
            minute = int(text[12:15])
        except ValueError:
            await message.answer(f'Не смог прочитать минуты напоминания: "{text[6:8]}"')
            return
    else:
        hour = 0
        minute = 0

    if 1 > day < 31:
        answer.append('\nДень месяца должен быть числом от 01 до 31')
    if 1 > month < 12:
        answer.append('\nМесяц должен быть числом от 01 до 12')
    if 1 > year < 99:
        answer.append(f'\nГод должен быть числом от {current.year} до {current.year+1}')
    if 0 > hour < 24:
        answer.append(f'\nЧас должен быть от 0 до 24')
    if 0 > minute < 60:
        answer.append(f'\nМинуты должны быть от 0 до 60')

    if answer:
        return answer

    return datetime(
        day=day,
        month=month,
        year=year+2000,
        hour=hour,
        minute=minute,
        tzinfo=Settings.timezone
    )


@form_router.message(NewReminderStates.new_date)
async def read_date(message: Message, state: FSMContext) -> None:
    date = (await state.get_data()).get('date')
    if date is None:
        date = await analyze_date(message)

    current = datetime.now(Settings.timezone)

    if isinstance(date, list):
        await message.answer(
            "Были встречены следующий ошибки при чтение даты и времени:"
            ''.join(date)
        )
        await state.set_state(NewReminderStates.main)
        return await new_reminder(message=message, state=state)
    if isinstance(date, datetime):
        if date.hour == 0 and date.minute == 0:
            date.replace(hour=current.hour, minute=current.minute)
        await message.answer(
            "Выбраны дата и время: "
            f'{date.day} {Settings.months[date.month]} {date:%Y} года {date:%H:%M}.'
            '\nВведите текст напоминания'
        )
        await state.set_state(NewReminderStates.text_date)
        return await state.set_data({'date': date})

    await new_date(message=message, state=state)


@form_router.message(NewReminderStates.text_date)
async def text_date(message: Message, state: FSMContext) -> None:
    date = (await state.get_data()).get('date')
    assert date is not None

    if len(message.text) > 2000:
        await message.answer("Слишком много символов")
        await read_date(message=message, state=state)

    reminder = await ReminderDB.new()
    reminder.datetime = date
    reminder.text = message.text
    reminder.owner = message.from_user.id
    await reminder.commit()

    await message.answer(
        f"Напоминание на {date.day} {Settings.months[date.month]}"
        f' успешно создано'
    )
    await state.set_data({'date': None})

    await Settings.main_menu(message=message, state=state)
