from typing import Any, List, Type, Union

T = Any


def ref(type_or_name: Union[str, Type[T]]) -> T:
    """
    When used as function, defines a reference to another object given
    a type or a name
    When used as method decorator, the method will return the instance
    of the desired object.
    DEPRECATED: Now uses type hints
    """
    if isinstance(type_or_name, str):
        return Dependency(type_or_name, None)
    return Dependency(None, type_or_name)


def refs(obj_type: Type[T]) -> List[T]:
    """
    All objects of a given type or subclasses of it.
    DEPRECATED: Now uses type hints
    """
    return Dependency(None, obj_type, Dependency.LIST)


class Dependency:

    SIMPLE = 1
    LIST = 2
    MAPPING = 3

    def __init__(self, name=None, type=None, ref_type=SIMPLE, key_type=None):
        self._name = name
        self._type = type
        self._ref_type = ref_type
        self._key_type = None

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def list_of_type(self):
        return self._ref_type == self.LIST

    @property
    def is_mapping(self):
        return self._ref_type == self.MAPPING

    @property
    def key_type(self):
        return self._key_type

    def __call__(self, func, *args, **kwargs):
        func._dependency = self
        return func

    def __str__(self):
        return f"Dependency(name={self._name},type={self._type},ref_type={self._ref_type})"

    def __iter__(self):
        """
        If not resolved, just emulate a dummy type.
        """
        return iter([])

    def __getattr__(self, key):
        raise AttributeError(f"Cannot get member {key} of unresolved dependency")
