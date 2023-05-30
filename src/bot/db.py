from typing import Optional, Self
from pathlib import Path
from sqlite3 import connect
from sqlite3 import Cursor as SQLCursor
from datetime import datetime, timedelta

from .settings import Settings


class Cursor:
    __slots__ = ('db', 'autocommit', '_cursor')

    def __init__(self, db: 'Database', autocommit: bool = False):
        self.db = db
        self.autocommit = autocommit
        self._cursor: Optional[SQLCursor] = None

    def __enter__(self) -> SQLCursor:
        assert self._cursor is None
        self._cursor = self.db.db.cursor()
        return self._cursor

    def __exit__(self, *_):
        self._cursor.close()
        if self.autocommit:
            self.db.db.commit()

    async def commit(self) -> Self:
        self.db.db.commit()
        return self


class Database:
    __slots__ = ('db', 'async_loop')

    def __init__(self, path: str | Path):
        if isinstance(path, Path):
            path = path.absolute()
        self.db = connect(path)

        with self.cursor() as cur:
            cur.execute('PRAGMA main.synchronous = NORMAL')
            cur.execute('PRAGMA main.journal_mode = OFF')
            cur.execute('PRAGMA temp_store = MEMORY')

            # Checking for tables in DB
            cur.execute(f"SELECT name FROM sqlite_master WHERE type = 'table'")
            tables = [table[0] for table in cur.fetchall()]

            if 'reminds' not in tables:
                cur.execute(f"""CREATE TABLE 'reminds'(
                    datetime REAL NOT NULL,
                    owner INTEGER NOT NULL,
                    text TEXT NOT NULL)""")

    def cursor(self, autocommit: bool = False) -> Cursor:
        return Cursor(db=self, autocommit=autocommit)

    async def unload_instance(self) -> None:
        self.unload_instance_normal()

    def unload_instance_normal(self) -> None:
        if self.db is None:
            return
        self.db.commit()
        self.db.close()
        self.db = None

class Reminder:
    __slots__ = ('id', '_loaded',
                 'datetime', 'owner', 'text',
                 '_datetime', '_owner', '_text')

    def __init__(self, id_: int):
        self._loaded = None
        self.id = id_
        self.datetime = None
        self.owner = None
        self.text = None

    async def get_by_id(self, id_: int):
        with Settings.Database.cursor() as cur:
            return cur.execute(
                "SELECT rowid, datetime, owner, text from 'reminds' "
                f"WHERE rowid == {id_}"
            ).fetchone()

    @classmethod
    async def new(cls) -> 'Reminder':
        with Settings.Database.cursor() as cur:
            cur: SQLCursor
            lastrowid = cur.execute(
                "SELECT rowid FROM 'reminds' ORDER BY rowid DESC LIMIT 1;"
            ).fetchone()
            if lastrowid is None:
                lastrowid = 1
            else:
                lastrowid = lastrowid[0]
            return Reminder(lastrowid+1)

    async def get(self, item):
        if item in self.__slots__:
            if item == 'id':
                return self.id
            else:
                if not self._loaded:
                    await self.load()
            return getattr(self, item)
        raise ValueError(f"There's no field {item} in reminder")

    async def load(self):
        db: Database = Settings.get('db')
        if db is None:
            raise RuntimeError('Trying to create reminder class '
                               'before database initialization')
        elif self.id is None:
            raise RuntimeError("Trying to run load with invalid id")
        reminder = await self.get_by_id(self.id)
        if not reminder:
            raise ValueError(f"Trying to get reminder with index {self.id} which doesn't exist")
        _, self.datetime, self.owner, self.text = reminder
        assert 'timezone' in Settings
        self.datetime = datetime.fromtimestamp(self.datetime, Settings.timezone)
        self._owner, self._datetime, self._text = self.owner, self.datetime, self.text
        self._loaded = True

    async def commit(self) -> None:

        # Types
        if isinstance(self.datetime, datetime):
            pass
        elif isinstance(self.datetime, float):
            self.datetime = datetime.fromtimestamp(
                self.datetime, Settings.timezone
            )
        else:
            raise ValueError("Datetime should be float or datetime object")
        if not isinstance(self.owner, int):
            raise ValueError("Owner ID should be integer")
        if not isinstance(self.text, str):
            raise ValueError("Text should be string")

        # Validators
        if len(self.text) > 2000:
            raise ValueError("Text of reminder shouldn't be above 2000 characters")

        date_limit = datetime.now(Settings.timezone)+ timedelta(days=366)
        if self.datetime.timestamp() > date_limit.timestamp():
            raise ValueError("Can't set reminder further than on year")

        datetime_float = self.datetime.timestamp()
        old_reminder = await self.get_by_id(self.id)
        if old_reminder is not None:
            command = (
                "UPDATE 'reminds'"
                "SET (datetime, owner, text)"
                " = (?, ?, ?) "
                f"WHERE rowid == {self.id}",
                (datetime_float, self.owner, self.text)
            )
        else:
            command = (
                "INSERT INTO 'reminds' "
                "(rowid, datetime, owner, text) "
                "VALUES (?, ?, ?, ?)",
                (self.id, datetime_float, self.owner, self.text)
            )
        with Settings.Database.cursor() as cur:
            return cur.execute(*command)


Settings.DB_Reminder = Reminder
