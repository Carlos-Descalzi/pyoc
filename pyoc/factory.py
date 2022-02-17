class FactoryDefinition:
    """
    Holds information about a given object factory.
    """

    def __init__(self, type_selector, factory_function, singleton):
        self._type_selector = type_selector
        self._factory_function = factory_function
        self._singleton = singleton

    def can_create(self, obj_type):
        return self._type_selector(obj_type)

    @property
    def factory_function(self):
        return self._factory_function

    @property
    def singleton(self):
        return self._singleton


class FactoryProxy:
    """
    Wraps a factory with information coming from context.
    """

    def __init__(self, context, func, obj_type):
        self._ctx = context
        self._func = func
        self._obj_type = obj_type

    def __call__(self, *args, **kwargs):
        """
        Factory callables must support two parameter:
            - the object type being created.
            - the context where it lives.
        """
        return self._func(self._obj_type, self._ctx)
