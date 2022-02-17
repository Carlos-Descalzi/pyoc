import inspect
import re
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Any, Callable, List, Type, TypeVar
from mock.mock import MagicMock
from .exceptions import DependencyError
from .wrapper import WrapperDefinition, Wrapper, WrapperChain
from .factory import FactoryDefinition, FactoryProxy
from .ref import Dependency

T = TypeVar("T", bound=object)


class Context:
    """
    Context class, holds all the objects and the information needed
    for instantiating them
    """

    def __init__(self):
        self._obj_types = []
        self._obj_type_dict = {}
        self._obj_type_name_dict = {}
        self._singletons = {}
        self._factories = []
        self._wrappers = []

    def close(self):
        for obj in self._singletons.values():
            if hasattr(obj, "release"):
                obj.release()
            del obj
        self._singletons.clear()

    def add(
        self, obj_type: Type, name: str = None, factory: Callable = None, lazy: bool = True, singleton: bool = False
    ):
        """
        Factory method (chainable) that adds a new dependency to the context to be resolved
        """
        self._obj_types.append(TypeDefinition(obj_type, name, lazy, singleton, factory))
        return self

    def add_object(self, obj: Any):
        """
        Adds an instance.
        """
        self._obj_types.append(TypeDefinition(obj.__class__, None, False, True, None))
        self._singletons[obj.__class__] = obj
        return self

    def add_factory(self, type_selector: Callable, factory_function: Callable, singleton: bool = False):
        """
        Adds a factory with a type selector.
        type_selector a function/or lambda with class as parameter, which returns True or False
        to determine if the factory is able to create the type.

        factory_function, a function that receives the class as parameter.
        """
        self._factories.append(FactoryDefinition(type_selector, factory_function, singleton))
        return self

    def wrap(self, obj_type: Type, method_expr: str, wrapper_type: Callable):
        """
        Adds a wrapper around a methods which match with a given regular expression in a given
        class.
        """
        self._wrappers.append(WrapperDefinition(obj_type, method_expr, wrapper_type))
        return self

    def get_by_type(self, obj_type: Type[T]) -> T:
        """
        Creates a new instance given an object type, which can be
        either the actual type requested, or a parent class.
        """
        actual_obj_type = self._find_type(obj_type)

        return self._instantiate_dependency(None, actual_obj_type)

    def get_all_by_type(self, obj_type: Type[T]) -> List[T]:
        """
        Gets instances of all objects of a given type, including subclasses
        """
        return [self._instantiate_dependency(None, t) for t in self._find_types(obj_type)]

    def get_by_expr(self, search_expr: Callable) -> Any:
        """
        Creates a new instance given a search expression over object types.
        Must be a function of type f(x) where x is the object type, and must return True/False.
        """
        actual_obj_type = self._find_type_by_expr(search_expr)

        if actual_obj_type:
            return self._get_instance(actual_obj_type)

        return None

    def get_by_name(self, obj_name: str) -> Any:
        """
        Creates a new instance given the name given to a class.
        To name classes, add a field NAME to it.
        """
        actual_obj_type = self._obj_type_name_dict.get(obj_name)
        if actual_obj_type:
            return self._get_instance(actual_obj_type)
        return None

    def process(self, obj_type: Type[T]) -> Type[T]:
        """
        Processes a class to prepare it to self resolve its dependencies once
        instantiated.
        """
        return self._process_type(obj_type)

    def new(self, obj_type: Type[T], *args, **kwargs) -> T:
        """
        Processes a given class, and returns a new instance with all its dependencies
        processed and ready to be resolved.
        """

        type_info = self._obj_type_dict.get(obj_type)

        if not type_info:
            processed_type = self._process_type(obj_type)
            type_info = TypeDefinition(obj_type, None, True, False, None)
            type_info.processed_type = processed_type
            self._obj_type_dict[obj_type] = type_info

        result = type_info.processed_type(*args, **kwargs)

        return result

    def get_type(self, obj_type: Type[T]) -> Type[T]:
        """
        Returns a processed type given the type already registered on it.
        The returned class will be able to resolve its dependencies once
        instantiated.
        """
        actual_obj_type = self._find_type(obj_type)
        if actual_obj_type:
            if actual_obj_type.processed_type():
                return actual_obj_type.processed_type()

            return obj_type
        return None

    def build(self):
        self._process_obj_types()
        return self

    def _get_instance(self, type_info):
        if type_info.factory:
            obj = type_info.factory(self)
        else:
            obj = type_info.processed_type()
        return obj

    def _instantiate_dependency(self, dependency, type_info):
        if isinstance(type_info, list):
            return [self._instantiate_dependency(dependency, t) for t in type_info]
        else:
            if type_info.singleton:
                instance = self._singletons.get(type_info.obj_type)
                if instance is None:
                    instance = self._get_instance(type_info)
                    self._singletons[type_info.obj_type] = instance
                return instance
            return self._get_instance(type_info)

    def _process_obj_types(self):
        for type_info in self._obj_types:
            obj_type = type_info.obj_type
            if not type_info.factory:
                type_info.processed_type = self._process_type(obj_type)
            else:
                if isinstance(type_info.factory, object):
                    type_info.factory = self._process_object(type_info.factory)
            if type_info.name:
                self._obj_type_name_dict[type_info.name] = type_info
            else:
                self._obj_type_name_dict[obj_type.__name__] = type_info
            self._obj_type_dict[obj_type] = type_info

    def _make_class_dict(self, obj_type):
        """
        I can't just copy obj_type.__dict__ because it doesn't give me the inherited members.
        TODO: That "as_view" is a workaround for flask to not break endpoints.
        """
        return {
            k: getattr(obj_type, k)
            for k in dir(obj_type)
            if
            # Workaround for Flask endpoints, the "as_view" doesn't respect the processed class
            # Will figure out a better solution later.
            k != "as_view"
        }

    def _process_type(self, obj_type):
        class_dict = self._make_class_dict(obj_type)

        def _getattr(obj, attr):
            result = obj_type.__getattribute__(obj, attr)
            if isinstance(result, Dependency):
                dependency_type = self._resolve_dependency_type(result)
                if dependency_type is None:
                    raise DependencyError(result._type, attr)
                return self._instantiate_dependency(result, dependency_type)
            else:
                if inspect.ismethod(result):
                    wrapper_types = getattr(obj, "__wrapper_types").get(attr)

                    if wrapper_types:
                        wrapper = getattr(obj, "__wrappers").get(attr)

                        if not wrapper:
                            wrapper = WrapperChain(result)

                            for wrapper_type in wrapper_types:
                                wrapper.add(self.new(wrapper_type, wrapper))
                            getattr(obj, "__wrappers")[attr] = wrapper

                        return wrapper
            return result

        wrapper_types = defaultdict(list)
        new_members = {}

        wrapper_infos = self._find_wrappers(obj_type)

        # Iterate through the class properties
        for name, member in class_dict.items():
            # If the item is a dependency to be resolved
            if self._hasattr(member, "_dependency"):
                # Resolve the dependency, allowing it to use __call__to instantiate
                new_members[name] = DependencyResolver(self, member, member._dependency)
            elif inspect.isfunction(member):
                for wrapper_info in wrapper_infos:
                    if wrapper_info and wrapper_info.matches(name):
                        wrapper_types[name].append(wrapper_info.wrapper_type)

        # For all the new dependencies found and resolved, add them by name to the class
        # allowing them to be accessed with ClassName.NameOfDependency
        class_dict.update(new_members)
        class_dict["__getattribute__"] = _getattr
        class_dict["__wrappers"] = {}
        class_dict["__wrapper_types"] = wrapper_types
        class_dict["__class__"] = obj_type

        return type(f"{obj_type.__name__}_New", (obj_type,), class_dict)

    def _process_object(self, obj):
        for key, val in obj.__class__.__dict__.items():
            if isinstance(val, Dependency):
                dependency_type = self._resolve_dependency_type(val)
                if not dependency_type:
                    raise DependencyError(val._type, key)
                dependency = self._instantiate_dependency(val, dependency_type)
                setattr(obj, key, dependency)

        return obj

    def _hasattr(self, member, name):
        # Skip mock objects in tests
        return not isinstance(member, MagicMock) and hasattr(member, name)

    def _resolve_dependency_type(self, dependency):
        if dependency.name:
            return self._obj_type_name_dict[dependency.name]
        elif dependency.type:
            if dependency.list_of_type:
                return self._find_types(dependency.type)
            return self._find_type(dependency.type)
        return None

    def _find_type(self, obj_type):
        try:
            return next(self._do_find_types(obj_type))
        except StopIteration:
            return None

    def _find_types(self, obj_type):
        return list(self._do_find_types(obj_type))

    def _do_find_types(self, obj_type):
        """
        Using a generator for performance reasons. When I need just first type
        I don't need to walk trough all the options.
        """
        result = self._obj_type_dict.get(obj_type)

        if result:
            yield result

        for item_key, item in self._obj_type_dict.items():
            if issubclass(item.obj_type, obj_type) or issubclass(item_key, obj_type):
                yield item

        for factory in self._factories:
            if factory.can_create(obj_type):
                yield TypeDefinition(
                    obj_type,
                    None,
                    True,
                    factory.singleton,
                    FactoryProxy(self, factory.factory_function, obj_type),
                )

    def _find_type_by_expr(self, search_expr):

        for obj_type, actual_type in self._obj_type_dict.items():
            if search_expr(obj_type):
                return actual_type

        return None

    def _find_wrappers(self, obj_type):
        return [wrapper for wrapper in self._wrappers if wrapper.valid_for_class(obj_type)]


class DependencyResolver:
    def __init__(self, ctx, member, dependency):
        self._ctx = ctx
        self._member = member
        self._dependency = dependency
        self._instance = None

    def __call__(self, *args, **kwargs):
        dependency_type = self._ctx._resolve_dependency_type(self._dependency)
        return self._ctx._instantiate_dependency(self._dependency, dependency_type)


class TypeDefinition:
    """
    Holds information about a given registered type.
    """

    def __init__(self, obj_type, name, lazy, singleton, factory):
        self.obj_type = obj_type
        self.name = name
        self.processed_type = None
        self.lazy = lazy
        self.singleton = singleton
        self.factory = factory
