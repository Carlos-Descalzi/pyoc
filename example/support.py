import sqlite3
import pyoc
from .ifces import UserService
from .impl import SQLUserDaoImpl, UserServiceImpl
from .wrapper import LogWrapper

DB_FILENAME = "sample.db"


class ConnectionFactory:
    def __init__(self, dbfilename):
        self._dbfilename = dbfilename

    def __call__(self, *_):
        return sqlite3.connect(self._dbfilename)


def build_context():
    return (
        pyoc.Context()
        .add_factory(lambda i: i == sqlite3.Connection, ConnectionFactory(DB_FILENAME))
        .add(SQLUserDaoImpl)
        .add(UserServiceImpl)
        .wrap(UserServiceImpl, ".*", LogWrapper)
        .build()
    )


def create_database():

    conn = sqlite3.connect(DB_FILENAME)

    c = conn.cursor()

    try:
        c.executescript(
            """
            drop table if exists users;
            create table users (
                id integer primary key not null,
                name varchar(30) not null
            );
        """
        )
    finally:
        c.close()
        conn.close()
