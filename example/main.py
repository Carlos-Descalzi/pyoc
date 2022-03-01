import sqlite3
import pyoc
import os
from .support import create_database, build_context
from .ifces import UserService
from .model import User
from .endpoints import build_app
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    create_database()

    ctx = build_context()

    user_service = ctx.get_by_type(UserService)

    user_service.save(User(name="Carlos"))
    user_service.save(User(name="Juan"))
    user_service.save(User(name="Pedro"))

    app = build_app(ctx)

    app.run(debug=True)
