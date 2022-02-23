from typing import Callable
from abc import ABCMeta, abstractmethod
import re


class WrapperDefinition:
    """
    Descrives a method wrapper or "AOP-around invoker"
    """

    def __init__(self, obj_type, method_expr, wrapper_type):
        self._obj_type = obj_type
        self._method_expr = method_expr
        self._wrapper_type = wrapper_type

    def valid_for_class(self, obj_type):
        return obj_type == self._obj_type or issubclass(obj_type, self._obj_type)

    def matches(self, method_name):
        return self._method_expr == method_name or re.match(self._method_expr, method_name) is not None

    @property
    def wrapper_type(self):
        return self._wrapper_type


class WrapperChain:
    """
    Merges all wrappers into one.
    Order of wrappers in list: first: outer most, last: inner-most.
    """

    def __init__(self, target):
        self._target = target
        self._wrappers = []

    def add(self, wrapper):
        self._wrappers.insert(0, wrapper)

    @property
    def target(self) -> Callable:
        return self._target

    def next(self, wrapper) -> Callable:
        index = self._wrappers.index(wrapper)
        if index == len(self._wrappers) - 1:
            return self._target
        return self._wrappers[index + 1]

    def __call__(self, *args, **kwargs):
        return self._wrappers[0](*args, **kwargs)

    def __str__(self):
        return f"WrapperChain, target:{self._target}, wrappers:[{map(str,self._wrappers)}]"


class Wrapper(metaclass=ABCMeta):
    """
    Base class for method wrappers.
    All wrappers must implement __call__ method, the wrapper chaining is done by
    calling self.next(*args,**kwargs)
    """

    def __init__(self, chain: WrapperChain):
        self._chain = chain

    @property
    def target(self) -> Callable:
        """
        Returns the actual target method being wrapped.
        """
        return self._chain.target

    def next(self, *args, **kwargs):
        """
        Invokes the next wrapper in the chain, or the target method if it
        is at the end of the chain.
        """
        return self._chain.next(self)(*args, **kwargs)

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass
