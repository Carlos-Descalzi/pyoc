from .model import User
from abc import ABCMeta, abstractmethod
from typing import List


class UserDao(metaclass=ABCMeta):
    @abstractmethod
    def get(self, id: int) -> User:
        pass

    @abstractmethod
    def save(self, obj: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        pass

    @abstractmethod
    def delete(self, id: int) -> User:
        pass


class UserService(metaclass=ABCMeta):
    @abstractmethod
    def get(self, id: int) -> User:
        pass

    @abstractmethod
    def save(self, obj: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        pass

    @abstractmethod
    def delete(self, id: int):
        pass
