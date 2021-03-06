"""Test exceptions for Byterun."""

import unittest

from pytype.tests import test_inference


class TestExceptions(test_inference.InferenceTest):

  def test_catching_exceptions(self):
    # TODO(kramm): Don't warn about NameErrors that are being caught.
    # Catch the exception precisely
    self.assertNoCrash("""\
      try:
        x[1]
        print("Shouldn't be here...")
      except NameError:
        print("caught it!")
      """)
    # Catch the exception by a parent class
    self.assertNoCrash("""\
      try:
        x[1]
        print("Shouldn't be here...")
      except Exception:
        print("caught it!")
      """)
    # Catch all exceptions
    self.assertNoCrash("""\
      try:
        x[1]
        print("Shouldn't be here...")
      except:
        print("caught it!")
      """)

  def test_raise_exception(self):
    self.assertNoErrors("raise Exception('oops')", raises=Exception)

  def test_raise_exception_class(self):
    self.assertNoErrors("raise ValueError", raises=ValueError)

  def test_raise_exception_2args(self):
    self.assertNoErrors("raise ValueError, 'bad'", raises=ValueError)

  def test_raise_exception_3args(self):
    self.assertNoErrors("""\
      from sys import exc_info
      try:
        raise Exception
      except:
        _, _, tb = exc_info()
      raise ValueError, "message", tb
      """, raises=ValueError)

  def test_raise_and_catch_exception(self):
    self.assertNoErrors("""\
      try:
        raise ValueError("oops")
      except ValueError as e:
        print("Caught: %s" % e)
      print("All done")
      """)

  @unittest.skip("Python 3 specific")
  def test_raise_exception_from(self):
    assert self.PYTHON_VERSION[0] == 3
    self.assertNoErrors(
        "raise ValueError from NameError",
        raises=ValueError
    )

  def test_raise_and_catch_exception_in_function(self):
    self.assertNoErrors("""\
      def fn():
        raise ValueError("oops")

      try:
        fn()
      except ValueError as e:
        print("Caught: %s" % e)
      print("done")
      """)

  def test_global_name_error(self):
    self.assertNoCrash("fooey", raises=NameError)
    # TODO(kramm): Don't warn about NameErrors that are being caught.
    self.assertNoCrash("""\
      try:
        fooey
        print("Yes fooey?")
      except NameError:
        print("No fooey")
      """)

  def test_local_name_error(self):
    self.assertNoCrash("""\
      def fn():
        fooey
      fn()
      """, raises=NameError)

  def test_catch_local_name_error(self):
    self.assertNoCrash("""\
      def fn():
        try:
          fooey
          print("Yes fooey?")
        except NameError:
          print("No fooey")
      fn()
      """)

  def test_reraise(self):
    self.assertNoCrash("""\
      def fn():
        try:
          fooey
          print("Yes fooey?")
        except NameError:
          print("No fooey")
          raise
      fn()
      """, raises=NameError)

  def test_reraise_explicit_exception(self):
    self.assertNoErrors("""\
      def fn():
        try:
          raise ValueError("ouch")
        except ValueError as e:
          print("Caught %s" % e)
          raise
      fn()
      """, raises=ValueError)

  def test_finally_while_throwing(self):
    self.assertNoErrors("""\
      def fn():
        try:
          print("About to..")
          raise ValueError("ouch")
        finally:
          print("Finally")
      fn()
      print("Done")
      """, raises=ValueError)

  def test_coverage_issue_92(self):
    self.assertNoErrors("""\
      l = []
      for i in range(3):
        try:
          l.append(i)
        finally:
          l.append('f')
        l.append('e')
      l.append('r')
      print(l)
      assert l == [0, 'f', 'e', 1, 'f', 'e', 2, 'f', 'e', 'r']
      """)

  def test_continue_in_except(self):
    self.assertNoErrors("""\
      for i in range(3):
        try:
          pass
        except:
          print i
          continue
        print 'e'
      """)

  def test_loop_finally_except(self):
    self.assertNoErrors("""
      def f():
        for s in (1, 2):
          try:
            try:
              break
            except:
              continue
          finally:
            pass
      """)

  def test_inherit_from_exception(self):
    ty = self.Infer("""
      class Foo(Exception):
        pass

      def bar(x):
        return Foo(x)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(Exception):
        pass

      def bar(x) -> Foo
    """)


if __name__ == "__main__":
  test_inference.main()
