"""Tests for union types."""

import unittest

from pytype.tests import test_inference


class SplitTest(test_inference.InferenceTest):
  """Tests for union types."""

  def testRestrictNone(self):
    ty = self.Infer("""
      def foo(x):
        y = str(x) if x else None

        if y:
          # y can't be None here!
          return y
        else:
          return 123
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def foo(x) -> Union[int, str]: ...
    """)

  def testRestrictTrue(self):
    ty = self.Infer("""
      def foo(x):
        y = str(x) if x else True

        if y:
          return 123
        else:
          return y
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def foo(x) -> Union[int, str]: ...
    """)

  def testRelatedVariable(self):
    ty = self.Infer("""
      def foo(x):
        # y is str or None
        # z is float or True
        if x:
          y = str(x)
          z = 1.23
        else:
          y = None
          z = True

        if y:
          # We only return z when y is true, so z must be a float here.
          return z

        return 123
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def foo(x) -> Union[float, int]: ...
    """)

  def testNestedConditions(self):
    ty = self.Infer("""
      def foo(x1, x2):
        y1 = str(x1) if x1 else 0

        if y1:
          if x2:
            return y1  # The y1 condition is still active here.

        return "abc"
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def foo(x1, x2) -> str: ...
    """)

  def testRemoveConditionAfterMerge(self):
    ty = self.Infer("""
      def foo(x):
        y = str(x) if x else None

        if y:
          # y can't be None here.
          z = 123
        # But y can be None here.
        return y
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def foo(x) -> Union[None, str]: ...
    """)

  def testUnsatisfiableCondition(self):
    # Check both sides of an "if".  If unsatisfiable code is executed then
    # it will result in an error due to unknown_method() and widen the return
    # signature to a Union.
    #
    # If a constant such as 0 or 1 is directly used as the condition of an
    # "if", then the compiler won't even generate bytecode for the branch
    # that isn't taken.  Thus the constant is first assigned to a variable and
    # the variable is used as the condition.  This is enough to fool the
    # compiler but pytype still figures out that one path is dead.
    ty = self.Infer("""
      def f1(x):
        c = 0
        if c:
          unknown_method()
          return 123
        else:
          return "hello"

      def f2(x):
        c = 1
        if c:
          return 123
        else:
          unknown_method()
          return "hello"

      def f3(x):
        c = 0
        if c:
          return 123
        else:
          return "hello"

      def f4(x):
        c = 1
        if c:
          return 123
        else:
          return "hello"
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def f1(x) -> str: ...
      def f2(x) -> int: ...
      def f3(x) -> str: ...
      def f4(x) -> int: ...
    """)

  def testShortCircuit(self):
    # Unlike normal if statement, the and/or short circuit logic does
    # not appear to be optimized away by the compiler.  Therefore these
    # simple tests do in fact execute if-splitting logic.
    ty = self.Infer("""
      def int_t(x): return 1 or x
      def int_f(x): return 0 and x
      def str_t(x): return "s" or x
      def str_f(x): return "" and x
      def bool_t(x): return True or x
      def bool_f(x): return False and x
      def tuple_t(x): return (1, ) or x
      def tuple_f(x): return () and x
      def dict_f(x): return {} and x
      def list_f(x): return [] and x
      def set_f(x): return set() and x
      def frozenset_f(x): return frozenset() and x
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def int_t(x) -> int: ...
      def int_f(x) -> int: ...
      def str_t(x) -> str: ...
      def str_f(x) -> str: ...
      def bool_t(x) -> bool: ...
      def bool_f(x) -> bool: ...
      def tuple_t(x) -> Tuple[int, ...]: ...
      def tuple_f(x) -> Tuple[nothing]: ...
      def dict_f(x) -> Dict[nothing, nothing]: ...
      def list_f(x) -> List[nothing]: ...
      def set_f(x) -> set[nothing]: ...
      def frozenset_f(x) -> frozenset[nothing]: ...
    """)

  def testDict(self):
    # Dicts start out as empty, which is compatible with False and not
    # compatible with True.  Any operation that possibly adds an item will
    # make the dict ambiguous - compatible with both True and False.
    ty = self.Infer("""
      def f1():
        d = {}
        return 123 if d else "hello"

      def f2(x):
        d = {}
        d[x] = x
        return 123 if d else "hello"
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def f1() -> str: ...
      def f2(x) -> Union[int, str]: ...
    """)

  @unittest.skip("Dict.update() doesn't establish a key parameter.")
  def testDictBroken(self):
    ty = self.Infer("""
      def f1():
        d = {}
        d.update({})
        return 123 if d else "hello"

      def f2():
        d = {}
        d.update({"a": 1})
        return 123 if d else "hello"

    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def f1() -> Union[int, str]: ...
      def f2() -> Union[int, str]: ...
    """)

  def testIsInstance(self):
    ty = self.Infer("""
      # Always returns a bool.
      def sig(x): return isinstance(x, str)
      # Cases where isinstance() can be determined, if-split will
      # narrow the return to a single type.
      def d1(): return "y" if isinstance("s", str) else 0
      def d2(): return "y" if isinstance("s", object) else 0
      def d3(): return "y" if isinstance("s", int) else 0
      def d4(): return "y" if isinstance("s", (float, str)) else 0
      # Cases where isinstance() is ambiguous.
      def a1(x): return "y" if isinstance(x, str) else 0
      def a2(x): return "y" if isinstance("a", 123) else 0
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def sig(x) -> bool: ...
      def d1() -> str: ...
      def d2() -> str: ...
      def d3() -> int: ...
      def d4() -> str: ...
      def a1(x) -> Union[int, str]: ...
      def a2(x) -> Union[int, str]: ...
    """)

  @unittest.skip("If-splitting isn't smart enough for this.")
  def testBroken(self):
    # TODO(dbaum): I don't think this test can work.
    ty = self.Infer("""
      def f2(x):
        if x:
          return x
        else:
          return 3j

      def f1(x):
        y = 1 if x else 0
        if y:
          return f2(y)
        else:
          return None
    """, deep=True, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      def f2(x) -> Any: ...
      def f1(x) -> Union[complex, int]: ...
    """)


if __name__ == "__main__":
  test_inference.main()
