"""Tests of selected stdlib functions."""

import unittest


from pytype.tests import test_inference


class StdlibTests(test_inference.InferenceTest):
  """Tests for files in typeshed/stdlib."""

  def testAST(self):
    ty = self.Infer("""
      import ast
      def f():
        return ast.parse("True")
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      ast = ...  # type: module
      def f() -> _ast.AST
    """)

  def testUrllib(self):
    ty = self.Infer("""
      import urllib
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      urllib = ...  # type: module
    """)

  def testTraceBack(self):
    ty = self.Infer("""
      import traceback
      def f(exc):
        return traceback.format_exception(*exc)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      traceback = ...  # type: module
      def f(exc) -> List[str]
    """)

  def testOsWalk(self):
    ty = self.Infer("""
      import os
      x = list(os.walk("/tmp"))
    """, deep=False, extract_locals=True)
    self.assertTypesMatchPytd(ty, """
      os = ...  # type: module
      x = ...  # type: List[Tuple[Union[str, unicode, List[Union[str, unicode]]], ...]]
    """)

  def testStruct(self):
    ty = self.Infer("""
      import struct
      x = struct.Struct("b")
    """, deep=False)
    self.assertTypesMatchPytd(ty, """
      struct = ...  # type: module
      x = ...  # type: struct.Struct
    """)

  @unittest.skip("Broken by typeshed upgrade")
  def testWarning(self):
    ty = self.Infer("""
      import warnings
    """, deep=False)
    self.assertTypesMatchPytd(ty, """
      warnings = ...  # type: module
    """)


if __name__ == "__main__":
  test_inference.main()
