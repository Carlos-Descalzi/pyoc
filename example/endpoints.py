from flask_restful import Resource, abort, request
import json
import pyoc
from . import model
from .ifces import UserService
from dataclasses import asdict
from flask import Flask
from flask_restful import Api


class Users(Resource):
    """
    Users endpoint
    """

    _user_service = pyoc.ref(UserService)

    def get(self):
        users = self._user_service.find_all()
        return list(map(asdict, users))

    def post(self):
        try:
            user_json = json.loads(request.data)
            user = model.User(**user_json)
            user = self._user_service.save(user)
            return asdict(user), 201
        except Exception as e:
            abort(500, str(e))


class User(Resource):
    """
    User endpoint
    """

    _user_service = pyoc.ref(UserService)

    def get(self, id):
        user = self._user_service.get(id)
        if user:
            return asdict(user)

        abort(404)

    def put(self, id):
        try:
            user_json = json.loads(request.data)
            user = self._user_service.get(id)
            user.name = user_json["name"]
            self._user_service.save(user)

            return None, 204
        except Exception as e:
            abort(500, str(e))

    def delete(self, id):
        self._user_service.delete(id)

        return None, 204


def build_app(ctx):
    app = Flask(__name__)
    api = Api(app)

    bp = pyoc.flask.BluePrint("main", __name__, "/", ctx)
    bp.add_endpoint(Users, "/users", methods=["GET", "POST"])
    bp.add_endpoint(User, "/users/<int:id>", methods=["GET", "DELETE", "PUT"])
    app.register_blueprint(bp)
    return app
