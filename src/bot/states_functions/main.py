"""
Contains start function
"""
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton

from ..settings import Settings


class Form(StatesGroup):
    main = State()


Settings.Form = Form


form_router: Dispatcher = Settings.Dispatcher


@form_router.message(Command('start'))
async def start(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    answer = 'Привет!' if current_state is None else 'Главное меню'
    await message.answer(
        answer,
        reply_markup=ReplyKeyboardMarkup(keyboard=[[
            KeyboardButton(text='Создать напоминание'),
            KeyboardButton(text='Просмотреть напоминания'),
        ]], resize_keyboard=True)
    )
    await state.set_state(Form.main)


Settings.main_menu = start


@form_router.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.main)
    await start(message=message, state=state)
