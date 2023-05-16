"""
Contains start function
"""
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..settings import Settings


form_router: Dispatcher = Settings['Dispatcher']


@form_router.message(Command('start'))
async def start(message: Message, state: FSMContext) -> None:
    await message.answer('Hello!')
    await state.set_state(Settings['Form'].main)
