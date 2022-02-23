import unittest
import pyoc
from flask_restful import Resource
from flask import Flask


class TestFlaskBlueprint(unittest.TestCase):
    def test_blueprint(self):
        class Service:
            def do_something(self):
                return "hello world"

        class SampleResource(Resource):

            _service: Service

            def get(self):
                return self._service.do_something(), 200

        ctx = pyoc.Context()
        ctx.add(Service)
        ctx.build()

        bp = pyoc.flask.BluePrint("main", __name__, "/", ctx)
        bp.add_endpoint(SampleResource, "/sample", methods=["GET"])

        app = Flask(__name__)
        app.register_blueprint(bp)

        client = app.test_client()

        res = client.get("/sample")

        self.assertEqual(b'"hello world"\n', res.data)
