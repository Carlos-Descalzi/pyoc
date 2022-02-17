import sqlite3
import pyoc
import os
from .support import create_database, build_context
from .ifces import UserService
from .model import User


if __name__ == "__main__":

    create_database()

    ctx = build_context()

    # Get an implementation of UserService interface
    user_service = ctx.get_by_type(UserService)

    user_service.save(User(name="Carlos"))
    user_service.save(User(name="Juan"))
    user_service.save(User(name="Pedro"))

    all_users = user_service.find_all()

    for user in all_users:
        print(f"User id:{user.id}, name:{user.name}")
