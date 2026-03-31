#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdestruct.c.struct_parser import definition_to_type


class StructParserTest(unittest.TestCase):
    """C struct parser tests."""

    def test_simple_struct(self):
        t = definition_to_type("struct Foo { int x; unsigned int y; };")
        self.assertIn("x", t.__annotations__)
        self.assertIn("y", t.__annotations__)

    def test_double_pointer(self):
        """Parser should handle double pointers (int **pp)."""
        t = definition_to_type("struct test { int **pp; };")
        self.assertIn("pp", t.__annotations__)

    def test_triple_pointer(self):
        t = definition_to_type("struct test { int ***ppp; };")
        self.assertIn("ppp", t.__annotations__)

    def test_array_field(self):
        t = definition_to_type("struct test { int arr[4]; };")
        self.assertIn("arr", t.__annotations__)

    def test_nested_struct_definition(self):
        t = definition_to_type("""
            struct inner { int x; };
            struct outer { struct inner a; int b; };
        """)
        self.assertIn("a", t.__annotations__)
        self.assertIn("b", t.__annotations__)


if __name__ == "__main__":
    unittest.main()
