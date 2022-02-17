from .context import Context
import flask
import flask_restful


class BluePrint(flask.Blueprint):
    """
    IOC support for Flask resources. Additionally, this class will add a field "app_context"
    to request objects.
    """

    def __init__(self, name: str, import_name: str, url_prefix: str, context: Context):
        """
        Parameters:
            name: Blueprint name
            import_name: may just be __name__
            url_prefix: The url prefix for the endpoints registered in the blueprint.
            context: the IOC context already configured.

        """
        super().__init__(name, import_name, url_prefix=url_prefix)
        self._context = context
        self._api = flask_restful.Api(self)
        self._api.app_context = context
        self.before_request(self._before_request)

    def add_endpoint(self, resource, *path_list, **kwargs):
        """
        Adds a resource. It processes the resource through the context to resolve references.
        Parameters:
            resource: The resource
            path_list: Paths associated to the resource
            kwargs: ... etc.
        """
        self._api.add_resource(self._context.process(resource), *path_list, **kwargs)

    def _before_request(self):
        flask.request.app_context = self._context
