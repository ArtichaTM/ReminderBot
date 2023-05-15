from typing import List
from asyncio import AbstractEventLoop, iscoroutinefunction
from threading import Thread
from datetime import datetime
from time import sleep

from .settings import Settings


_MINUTE_CHANGE_NOTIFY_LIST: List[callable] = []


def _cycle():
    assert hasattr(Settings, 'loop'), "Settings doesn't have asyncio loop"
    loop: AbstractEventLoop = Settings.loop
    while True:
        sleep(60 - datetime.now().second)
        for func in _MINUTE_CHANGE_NOTIFY_LIST:
            assert iscoroutinefunction(func), "All function in list should be asynchronous"
            loop.create_task(func())


def start_cycle():
    Thread(target=_cycle, daemon=True).start()


Settings.minute_notify_list = _MINUTE_CHANGE_NOTIFY_LIST
