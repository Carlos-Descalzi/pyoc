import inspect
import re
from abc import ABCMeta, abstractmethod
from collections import defaultdict
import typing
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
        Add an object to the context, which can be a concrete type, or a factory.
        Parameters:
            obj_type: the object class to add. If a factory is used, this can be the parent class of the
                object provided by the factory.
            name: An optional name if the object is intended to be resolved by name.
            factory: (optional) a Callable which provides instances of this object.
            lazy: create the object on demand or when context is built.
            singleton: specifies if it is a singleton or new instances must be
                returned all the time.
        Return value:
            the desired object.
        """
        self._obj_types.append(TypeDefinition(obj_type, name, lazy, singleton, factory))
        return self

    def add_object(self, obj: Any):
        """
        Adds an object instance. This object will behave as a singleton.
        Parameters:
            obj: The object to add to the context.
        """
        self._obj_types.append(TypeDefinition(obj.__class__, None, False, True, None))
        self._singletons[obj.__class__] = obj
        return self

    def add_factory(self, type_selector: Callable, factory_function: Callable, singleton: bool = False):
        """
        Adds a factory with a type selector.
        Parameters:
            type_selector: a callable which receives the requested class as parameter, must return True or False
                to determine if the factory is able to create the type.

            factory_function: A callable that receives the class and the context as parameters, must provide
                and object.
        """
        self._factories.append(FactoryDefinition(type_selector, factory_function, singleton))
        return self

    def wrap(self, obj_type: Type, method_expr: str, wrapper_type: Callable):
        """
        Adds a wrapper callable around a methods which match with a given regular expression in a given
        class.
        """
        self._wrappers.append(WrapperDefinition(obj_type, method_expr, wrapper_type))
        return self

    def get_by_type(self, obj_type: Type[T]) -> T:
        """
        Returns an object of the desired type, which can be the exact class or a subclass.
        """
        actual_obj_type = self._find_type(obj_type)

        return self._instantiate_dependency(None, actual_obj_type)

    def get_all_by_type(self, obj_type: Type[T]) -> List[T]:
        """
        Returns all objects of the desired type, including subclasses
        """
        return [self._instantiate_dependency(None, t) for t in self._find_types(obj_type)]

    def get_by_expr(self, search_expr: Callable) -> Any:
        """
        Creates a new instance given a search expression over object types.
        Must be a callable which receives as parameter a type and return True or False.
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
        elif isinstance(type_info, dict):
            return {k: self._instantiate_dependency(dependency, v) for k, v in type_info.items()}
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

    def _is_list_type(self, attr):
        return isinstance(attr, typing._GenericAlias) and attr._name == "List"

    def _is_mapping_type(self, attr):
        return isinstance(attr, typing._GenericAlias) and attr._name == "Mapping"

    def _resolve_attr(self, obj, obj_type, attr_name):

        annotations = obj_type.__dict__.get("__annotations__", {})

        annotation = annotations.get(attr_name)
        if annotation:
            if inspect.isclass(annotation):
                return Dependency(None, annotation)
            elif self._is_list_type(annotation):
                arg_types = annotation.__args__
                if arg_types:
                    return Dependency(None, arg_types[0], Dependency.LIST)
            elif self._is_mapping_type:
                arg_types = annotation.__args__
                if arg_types:
                    key_type, val_type = arg_types
                    return Dependency(None, val_type, Dependency.MAPPING, key_type)

        attr = obj_type.__getattribute__(obj, attr_name)

        return attr

    def _process_type(self, obj_type):
        class_dict = self._make_class_dict(obj_type)

        def _getattr(obj, attr):
            result = self._resolve_attr(obj, obj_type, attr)
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

        for name, member in class_dict.items():
            if self._hasattr(member, "_dependency"):
                new_members[name] = DependencyResolver(self, member, member._dependency)
            elif inspect.isfunction(member):
                for wrapper_info in wrapper_infos:
                    if wrapper_info and wrapper_info.matches(name):
                        wrapper_types[name].append(wrapper_info.wrapper_type)

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
        return not isinstance(member, MagicMock) and hasattr(member, name)

    def _resolve_dependency_type(self, dependency):
        if dependency.name:
            return self._obj_type_name_dict[dependency.name]
        elif dependency.type:
            if dependency.list_of_type:
                return self._find_types(dependency.type)
            elif dependency.is_mapping:
                return {t.name: t for t in self._find_types(dependency.type) if t.name}
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
        all_items = set()
        result = self._obj_type_dict.get(obj_type)

        if result:
            all_items.add(result)
            yield result

        for item_key, item in self._obj_type_dict.items():
            if (issubclass(item.obj_type, obj_type) or issubclass(item_key, obj_type)) and item not in all_items:
                all_items.add(item)
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
