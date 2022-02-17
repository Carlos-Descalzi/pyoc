from typing import Callable, Type, Any, List

T = Any


def ref(type_or_name):
    """
    When used as function, defines a reference to another object given
    a type or a name
    When used as method decorator, the method will return the instance
    of the desired object.

    """
    if isinstance(type_or_name, str):
        return Dependency(type_or_name, None)
    return Dependency(None, type_or_name)


def refs(obj_type: Type[T]) -> List[T]:
    """
    All objects of a given type or subclasses of it.
    """
    return Dependency(None, obj_type, True)


class Dependency:
    def __init__(self, name=None, type=None, list_of_type=False):
        self._name = name
        self._type = type
        self._list_of_type = list_of_type

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def list_of_type(self):
        return self._list_of_type

    def __call__(self, func, *args, **kwargs):
        func._dependency = self
        return func

    def __str__(self):
        return f"Dependency(name={self._name},type={self._type},list_of_type={self._list_of_type})"

    def __iter__(self):
        """
        If not resolved, just emulate a dummy type.
        """
        return iter([])

    def __getattr__(self, key):
        raise AttributeError(f"Cannot get member {key} of unresolved dependency")
