"""
Contains states class
"""
from aiogram.fsm.state import State, StatesGroup

from ..settings import Settings


class Form(StatesGroup):
    main = State()


Settings['Form'] = Form
