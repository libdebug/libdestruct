#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest

from libdestruct.c.struct_parser import definition_to_type
from libdestruct import inflater


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


class TypedefTest(unittest.TestCase):
    """Typedef support in C struct parser."""

    def test_simple_typedef(self):
        t = definition_to_type("""
            typedef unsigned int uint32_t;
            struct S { uint32_t x; };
        """)
        self.assertIn("x", t.__annotations__)

    def test_typedef_of_struct(self):
        t = definition_to_type("""
            typedef struct { int x; } Point;
            struct S { Point p; };
        """)
        self.assertIn("p", t.__annotations__)

    def test_typedef_of_pointer(self):
        t = definition_to_type("""
            typedef int *intptr;
            struct S { intptr p; };
        """)
        self.assertIn("p", t.__annotations__)

    def test_typedef_chain(self):
        t = definition_to_type("""
            typedef unsigned int u32;
            typedef u32 mytype;
            struct S { mytype x; };
        """)
        self.assertIn("x", t.__annotations__)

    def test_typedef_inflate_and_read(self):
        t = definition_to_type("""
            typedef unsigned int uint32_t;
            struct S { uint32_t x; int y; };
        """)
        memory = bytearray(8)
        memory[0:4] = pystruct.pack("<I", 0xDEADBEEF)
        memory[4:8] = pystruct.pack("<i", -42)

        lib = inflater(memory)
        s = lib.inflate(t, 0)
        self.assertEqual(s.x.value, 0xDEADBEEF)
        self.assertEqual(s.y.value, -42)


if __name__ == "__main__":
    unittest.main()
