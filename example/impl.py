from .model import User
from .ifces import UserDao, UserService
import sqlite3
from typing import List


class SQLUserDaoImpl(UserDao):

    _conn: sqlite3.Connection

    def get(self, id: int) -> User:

        c = self._conn.cursor()
        try:
            c.execute("select id, name from users where id = ?", (id,))

            for id, name in c.fetchall():
                return User(id, name)
        finally:
            c.close()

        return None

    def save(self, user: User) -> User:
        c = self._conn.cursor()

        try:

            if not user.id:
                c.execute("insert into users(name) values (?)", (user.name,))
                c.execute("select last_insert_rowid()")
                id = c.fetchone()
                user.id = id[0]
            else:
                c.execute("update users set name = ? where id = ?", (user.name, user.id))
            c.execute("commit")

        finally:
            c.close()

        return user

    def find_all(self) -> List[User]:
        c = self._conn.cursor()
        try:
            c.execute("select id, name from users")
            return [User(id, name) for id, name in c.fetchall()]
        finally:
            c.close()

    def delete(self, id: int) -> User:
        c = self._conn.cursor()
        try:
            c.execute("delete from users where id = ?", (id,))
            c.execute("commit")
        finally:
            c.close()


class UserServiceImpl(UserService):

    _dao: UserDao

    def get(self, id: int) -> User:
        return self._dao.get(id)

    def save(self, obj: User) -> User:
        return self._dao.save(obj)

    def find_all(self) -> List[User]:
        return self._dao.find_all()

    def delete(self, id: int):
        self._dao.delete(id)
