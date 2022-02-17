from .context import Context
from flask import Blueprint, request
import flask_restful


class ContextAwareBluePrint(Blueprint):
    def __init__(self, name: str, import_name: str, url_prefix: str, context: Context):
        super().__init__(name, import_name, url_prefix=url_prefix)
        self._context = context
        self._api = flask_restful.Api(self)
        self._api.app_context = context
        self.before_request(self._before_request)

    def add_endpoint(self, resource, *path_list, **kwargs):
        self._api.add_resource(self._context.process(resource), *path_list, **kwargs)

    def _before_request(self):
        request.app_context = self._context
