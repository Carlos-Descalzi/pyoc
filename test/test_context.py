import unittest
import pyoc


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

        obj = context.get_by_type(Object2)
        self.assertIsNotNone(obj)

        result = obj.do_something()
        self.assertEqual("done", result)

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

        obj = context.get_by_type(Object4)

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

        obj = context.get_by_type(Object4)

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
