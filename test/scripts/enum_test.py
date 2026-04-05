#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from enum import Enum, IntEnum
from libdestruct import inflater, c_int, enum, enum_of, struct

class EnumTest(unittest.TestCase):
    def test_enum(self):
        class Test(IntEnum):
            A = 0
            B = 1
            C = 2
            D = 3

        libdestruct = inflater((0).to_bytes(4, "little"))

        a = libdestruct.inflate(enum_of(Test), 0)

        self.assertEqual(a.value, Test.A)

        self.assertEqual(bytes(a), b"\x00\x00\x00\x00")

        class TestHolder(struct):
            a: enum = enum_of(Test)
            b: enum = enum_of(Test)
            c: enum = enum_of(Test)
            d: enum = enum_of(Test)

        libdestruct = inflater(b"".join(i.to_bytes(4, "little") for i in range(4)))

        test = libdestruct.inflate(TestHolder, 0)

        self.assertEqual(test.a.value, Test.A)
        self.assertEqual(test.b.value, Test.B)
        self.assertEqual(test.c.value, Test.C)
        self.assertEqual(test.d.value, Test.D)

        self.assertEqual(bytes(test), b"".join(i.to_bytes(4, "little") for i in range(4)))

        with self.assertRaises(TypeError):
            enum_of(Enum)

        # Let's try with enums of different sizes
        class TestHolder2(struct):
            a: enum = enum_of(Test, size=1)
            b: enum = enum_of(Test, size=2)
            c: enum = enum_of(Test, size=4)
            d: enum = enum_of(Test, size=8)

        memory = (1).to_bytes(1, "little") + (2).to_bytes(2, "little") + (3).to_bytes(4, "little") + (3).to_bytes(8, "little")

        libdestruct = inflater(memory)

        test = libdestruct.inflate(TestHolder2, 0)

        self.assertEqual(test.a.value, Test.B)
        self.assertEqual(test.b.value, Test.C)
        self.assertEqual(test.c.value, Test.D)
        self.assertEqual(test.d.value, Test.D)

        self.assertEqual(bytes(test), memory)

        with self.assertRaises(ValueError):
            enum_of(Test, size=3)

        with self.assertRaises(ValueError):
            enum_of(Test, size=9)

    def test_enum_to_str_no_leading_indent(self):
        """enum.to_str() should not add unexpected leading indentation."""
        class Color(IntEnum):
            RED = 0
            GREEN = 1

        class test_t(struct):
            color: enum = enum_of(Color)
            x: c_int

        memory = b""
        memory += (1).to_bytes(4, "little")  # GREEN
        memory += (42).to_bytes(4, "little")

        test = test_t.from_bytes(memory)
        result = test.to_str()

        # Should be "    color: <Color.GREEN: 1>", not "    color:     <Color.GREEN: 1>"
        self.assertIn("color: <Color.GREEN: 1>", result)

    def test_enum_standalone_to_str(self):
        class Color(IntEnum):
            RED = 0
            BLUE = 1

        class test_t(struct):
            color: enum = enum_of(Color)

        memory = (0).to_bytes(4, "little")
        test = test_t.from_bytes(memory)

        result = test.color.to_str()
        self.assertFalse(result.startswith(" "))

    def test_enum_value_extraction(self):
        class Status(IntEnum):
            OK = 0
            ERROR = 1
            PENDING = 2

        class test_t(struct):
            status: enum = enum_of(Status)

        memory = (2).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.status.value, Status.PENDING)

    def test_bytes_on_bytearray_backed_enum(self):
        class Color(IntEnum):
            RED = 0
            GREEN = 1

        class test_t(struct):
            color: enum = enum_of(Color)

        lib = inflater(bytearray(b"\x01\x00\x00\x00"))
        test = lib.inflate(test_t, 0)

        result = bytes(test)
        self.assertIsInstance(result, bytes)
