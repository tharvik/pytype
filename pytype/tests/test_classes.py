"""Tests for classes."""

import unittest

from pytype.tests import test_inference


class ClassesTest(test_inference.InferenceTest):
  """Tests for classes."""

  def testClassDecorator(self):
    ty = self.Infer("""
      @__any_object__
      class MyClass(object):
        def method(self, response):
          pass
      def f():
        return MyClass()
    """, deep=True, solve_unknowns=True, extract_locals=False)
    self.assertTypesMatchPytd(ty, """
      # "function" because it gets called in f()
      MyClass = ...  # type: function
      def f() -> ?
    """)

  def testClassName(self):
    ty = self.Infer("""
      class MyClass(object):
        def __init__(self, name):
          pass
      def f():
        factory = MyClass
        return factory("name")
      f()
    """, deep=False, solve_unknowns=False, extract_locals=False)
    self.assertTypesMatchPytd(ty, """
    class MyClass(object):
      def __init__(self, name: str) -> NoneType

    def f() -> MyClass
    """)

  def testInheritFromUnknown(self):
    ty = self.Infer("""
      class A(__any_object__):
        pass
    """, deep=False, solve_unknowns=False, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
    class A(?):
      pass
    """)

  def testInheritFromUnknownAndCall(self):
    ty = self.Infer("""
      x = __any_object__
      class A(x):
        def __init__(self):
          x.__init__(self)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    x = ...  # type: ?
    class A(?):
      def __init__(self) -> NoneType
    """)

  def testInheritFromUnknownAndSetAttr(self):
    ty = self.Infer("""
      class Foo(__any_object__):
        def __init__(self):
          setattr(self, "test", True)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    class Foo(?):
      def __init__(self) -> NoneType
    """)

  def testClassMethod(self):
    ty = self.Infer("""
      module = __any_object__
      class Foo(object):
        @classmethod
        def bar(cls):
          module.bar("", '%Y-%m-%d')
      def f():
        return Foo.bar()
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    module = ...  # type: ?
    def f() -> NoneType
    class Foo(object):
      # TODO(kramm): pytd needs better syntax for classmethods
      bar = ...  # type: classmethod
    """)

  def testInheritFromUnknownAttributes(self):
    ty = self.Infer("""
      class Foo(__any_object__):
        def f(self):
          self.x = [1]
          self.y = list(self.x)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    class Foo(?):
      x = ...  # type: List[int, ...]
      y = ...  # type: List[int, ...]
      def f(self) -> NoneType
    """)

  def testInnerClass(self):
    ty = self.Infer("""
      def f():
        class Foo(object):
          x = 3
        l = Foo()
        return l.x
    """, deep=True, solve_unknowns=False, extract_locals=False)
    self.assertTypesMatchPytd(ty, """
      def f() -> int
    """)

  def testSuper(self):
    ty = self.Infer("""
      class Base(object):
        def __init__(self, x, y):
          pass
      class Foo(Base):
        def __init__(self, x):
          super(Foo, self).__init__(x, y='foo')
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    class Base(object):
      def __init__(self, x, y) -> NoneType
    class Foo(Base):
      def __init__(self, x) -> NoneType
    """)

  @unittest.skip("Fails, needs 'raises' support.")
  def testSuperError(self):
    self.assertNoErrors("""
      class Base(object):
        def __init__(self, x, y, z):
          pass
      class Foo(Base):
        def __init__(self, x):
          super(Foo, self).__init__()
    """, raises=ValueError)

  def testSuperInInit(self):
    ty = self.Infer("""
      class A(object):
        def __init__(self):
          self.x = 3

      class B(A):
        def __init__(self):
          super(B, self).__init__()

        def get_x(self):
          return self.x
    """, deep=True, solve_unknowns=False, extract_locals=False)
    self.assertTypesMatchPytd(ty, """
        class A(object):
          x = ...  # type: int

        class B(A):
          # TODO(kramm): optimize this out
          x = ...  # type: int
          def get_x(self) -> int
    """)

  def testSuperDiamond(self):
    ty = self.Infer("""
      class A(object):
        x = 1
      class B(A):
        y = 4
      class C(A):
        y = "str"
        z = 3j
      class D(B, C):
        def get_x(self):
          return super(D, self).x
        def get_y(self):
          return super(D, self).y
        def get_z(self):
          return super(D, self).z
    """, deep=True, solve_unknowns=False, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      class A(object):
          x = ...  # type: int
      class B(A):
          y = ...  # type: int
      class C(A):
          y = ...  # type: str
          z = ...  # type: complex
      class D(B, C):
          def get_x(self) -> int
          def get_y(self) -> int
          def get_z(self) -> complex
    """)

  def testInheritFromList(self):
    ty = self.Infer("""
      class MyList(list):
        def foo(self):
          return getattr(self, '__str__')
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class MyList(List[?, ...]):
        def foo(self) -> ?
    """)

  def testClassAttr(self):
    ty = self.Infer("""
      class Foo(object):
        pass
      OtherFoo = Foo().__class__
      Foo.x = 3
      OtherFoo.x = "bar"
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        # TODO(kramm): should be just "str". Also below.
        x = ...  # type: int or str
      # TODO(kramm): Should this be an alias?
      class OtherFoo(object):
        x = ...  # type: int or str
    """)

  def testBoundMethod(self):
    ty = self.Infer("""
      class Random(object):
          def seed(self):
            pass

<<<<<<< 1cfc23e744426c9df3f023a6500a78fbcaa65608
      _inst = Random()
      seed = _inst.seed
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    class Random(object):
       def seed(self) -> None: ...

    _inst = ...  # type: Random
    seed = ...  # type: function
    """)

  def testMROWithUnsolvables(self):
    ty = self.Infer("""
      from nowhere import X, Y  # pytype: disable=import-error
      class Foo(Y):
        pass
      class Bar(X, Foo, Y):
        pass
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      X = ...  # type: ?
      Y = ...  # type: ?
      class Foo(?):
        ...
      class Bar(?, Foo, ?):
        ...
    """)

  def testProperty(self):
    ty = self.Infer("""
      class Foo(object):
        def __init__(self):
          self._name = "name"
        def test(self):
          return self.name
        name = property(fget=lambda self: self._name)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        _name = ...  # type: str
        name = ...  # type: property
        def test(self) -> str: ...
    """)

  def testDescriptorSelf(self):
    ty = self.Infer("""
      class Foo(object):
        def __init__(self):
          self._name = "name"
        def __get__(self, obj, objtype):
          return self._name
      class Bar(object):
        def test(self):
          return self.foo
        foo = Foo()
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        _name = ...  # type: str
        def __get__(self, obj, objtype) -> str: ...
      class Bar(object):
        foo = ...  # type: Foo
        def test(self) -> str: ...
    """)

  def testDescriptorInstance(self):
    ty = self.Infer("""
      class Foo(object):
        def __get__(self, obj, objtype):
          return obj._name
      class Bar(object):
        def __init__(self):
          self._name = "name"
        def test(self):
          return self.foo
        foo = Foo()
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        def __get__(self, obj, objtype) -> Any: ...
      class Bar(object):
        _name = ...  # type: str
        foo = ...  # type: Foo
        def test(self) -> str: ...
    """)

  def testDescriptorClass(self):
    ty = self.Infer("""
      class Foo(object):
        def __get__(self, obj, objtype):
          return objtype._name
      class Bar(object):
        def test(self):
          return self.foo
        _name = "name"
        foo = Foo()
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        def __get__(self, obj, objtype) -> Any: ...
      class Bar(object):
        _name = ...  # type: str
        foo = ...  # type: Foo
        def test(self) -> str: ...
    """)
=======
  def testClassAttr(self):
    with self.Infer("""
      class Foo(object):
        pass
      OtherFoo = Foo().__class__
      Foo.x = 3
      OtherFoo.x = "bar"
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
        class Foo(object):
          # TODO(kramm): should be just "str". Also below.
          x = ...  # type: int or str
        # TODO(kramm): Should this be an alias?
        class OtherFoo(object):
          x = ...  # type: int or str
      """)

>>>>>>> Add support for __class__.

  def testGetAttr(self):
    ty = self.Infer("""
      class Foo(object):
        def __getattr__(self, name):
          return "attr"
      def f():
        return Foo().foo
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        def __getattr__(self, name) -> str: ...
      def f() -> str: ...
    """)

if __name__ == "__main__":
  test_inference.main()
