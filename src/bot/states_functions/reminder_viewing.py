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
from .states_class import Form


form_router: Dispatcher = Settings.Dispatcher


@form_router.message(
    Form.main,
    F.text.casefold() == 'просмотреть напоминания'
)
async def new_reminder(message: Message, state: FSMContext) -> None:
    await message.answer(
        '?',
        reply_markup=ReplyKeyboardMarkup(keyboard=[[
            KeyboardButton(text='В определённую дату'),
            KeyboardButton(text='Через определённый промежуток времени'),
        ]], resize_keyboard=True)
    )
    await state.set_state(Form.main)
