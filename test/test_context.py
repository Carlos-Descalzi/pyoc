import unittest
import pyoc
from typing import List, Mapping


class TestContext(unittest.TestCase):
    def test_simple_initialization(self):
        class Object1:
            def do_something(self):
                return "done"

        class Object2:
            object_1 = pyoc.ref(Object1)

            def do_something(self):
                return self.object_1.do_something()

        context = pyoc.Context().add(Object1).add(Object2).build()

        obj = context.get(Object2)
        self.assertIsNotNone(obj)

        result = obj.do_something()
        self.assertEqual("done", result)

    def test_simple_initialization_hint(self):
        class Object1:
            def do_something(self):
                return "done"

        class Object2:
            object_1: Object1

            def do_something(self):
                return self.object_1.do_something()

        context = pyoc.Context().add(Object1).add(Object2).build()

        obj = context.get(Object2)
        self.assertIsNotNone(obj)

        result = obj.do_something()
        self.assertEqual("done", result)

    def test_simple_initialization_hint_list(self):
        class Object1:
            def do_something(self):
                return "done"

        class Object2:
            object_1: List[Object1]

            def do_something(self):
                return self.object_1.do_something()

        context = pyoc.Context().add(Object1).add(Object2).build()

        obj = context.get(Object2)
        self.assertIsNotNone(obj)
        v = obj.object_1
        self.assertIsInstance(v, list)
        self.assertEqual(1, len(v))
        self.assertIsInstance(v[0], Object1)

    def test_simple_initialization_hint_mapping(self):
        class Object1:
            def do_something(self):
                return "done"

        class Object2:
            object_1: Mapping[str, Object1]

            def do_something(self):
                return self.object_1.do_something()

        context = pyoc.Context().add(Object1, name="obj_1").add(Object2).build()

        obj = context.get(Object2)
        self.assertIsNotNone(obj)
        self.assertIsInstance(obj.object_1, dict)
        self.assertIn("obj_1", obj.object_1)
        self.assertIsInstance(obj.object_1["obj_1"], Object1)

    def test_no_singleton(self):
        class Object3:
            count = 0

            def do_something(self):
                self.count += 1
                return self.count

        class Object4:
            object_3 = pyoc.ref(Object3)

            def do_something(self):
                return self.object_3.do_something()

        context = pyoc.Context().add(Object3).add(Object4).build()

        obj = context.get(Object4)

        self.assertEqual(1, obj.do_something())
        self.assertEqual(1, obj.do_something())

    def test_singleton(self):
        class Object3:
            count = 0

            def do_something(self):
                self.count += 1
                return self.count

        class Object4:
            object_3 = pyoc.ref(Object3)

            def do_something(self):
                return self.object_3.do_something()

        context = pyoc.Context().add(Object3, singleton=True).add(Object4).build()

        obj = context.get(Object4)

        self.assertEqual(1, obj.do_something())
        self.assertEqual(2, obj.do_something())

    def test_hierarchy(self):
        class Parent:
            pass

        class Child1(Parent):
            pass

        class Child2(Parent):
            pass

        context = pyoc.Context().add(Child1).add(Child2).build()

        objs = context.get_all_by_type(Parent)

        self.assertEqual(2, len(objs))

    def test_wrapper(self):
        class Obj:
            def return_something(self):
                return 1

        class MyWrapper(pyoc.Wrapper):
            def __call__(self):
                return self.next() + 1

        class MyWrapper2(pyoc.Wrapper):
            def __call__(self):
                return self.next() * -1

        context = pyoc.Context()
        context.add(Obj)
        context.wrap(Obj, ".*", MyWrapper)
        context.wrap(Obj, ".*", MyWrapper2)
        context.build()

        obj = context.get(Obj)

        self.assertEqual(-2, obj.return_something())
