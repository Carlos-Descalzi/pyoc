import unittest
import pyoc
from typing import List, Mapping


class TestFactory(unittest.TestCase):
    def test_factory_type(self):
        class Obj:
            pass

        class Obj2:
            pass

        context = pyoc.Context()
        context.add(Obj, factory=lambda x: Obj())
        context.build()

        obj = context.get(Obj)

        self.assertIsNotNone(obj)
        self.assertIsInstance(obj, Obj)

        obj = context.get(Obj2)
        self.assertIsNone(obj)

    def test_factory_selector(self):
        class Obj:
            pass

        context = pyoc.Context()
        context.add_factory(lambda x: x == Obj, lambda t, c: Obj())
        context.build()

        obj = context.get(Obj)
        self.assertIsNotNone(obj)
        self.assertIsInstance(obj, Obj)

        obj = context.get(str)
        self.assertIsNone(obj)
