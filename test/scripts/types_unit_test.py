#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import ctypes
import math
import struct as pystruct
import unittest

from libdestruct import c_int, c_long, c_str, c_uint, c_float, c_double, inflater, struct, ptr, ptr_to_self


class ObjFromBytesTest(unittest.TestCase):
    """obj.from_bytes() for non-struct types."""

    def test_c_int_from_bytes(self):
        data = (42).to_bytes(4, "little")
        obj = c_int.from_bytes(data)
        self.assertEqual(obj.value, 42)

    def test_c_long_from_bytes(self):
        data = (123456789).to_bytes(8, "little")
        obj = c_long.from_bytes(data)
        self.assertEqual(obj.value, 123456789)

    def test_c_uint_from_bytes(self):
        data = (0xDEADBEEF).to_bytes(4, "little")
        obj = c_uint.from_bytes(data)
        self.assertEqual(obj.value, 0xDEADBEEF)


class CtypesGenericFrozenTest(unittest.TestCase):
    """ctypes generic frozen to_bytes."""

    def test_frozen_to_bytes(self):
        memory = (42).to_bytes(ctypes.sizeof(ctypes.c_int), "little")
        lib = inflater(memory)
        obj = lib.inflate(ctypes.c_int, 0)

        self.assertEqual(obj.value, 42)
        obj.freeze()
        self.assertEqual(obj.value, 42)
        self.assertEqual(len(obj.to_bytes()), ctypes.sizeof(ctypes.c_int))
        self.assertEqual(obj.to_bytes(), memory)


class FreezeTest(unittest.TestCase):
    """Freeze semantics for primitive types."""

    def test_frozen_c_int_rejects_writes(self):
        data = (99).to_bytes(4, "little")
        obj = c_int.from_bytes(data)

        self.assertTrue(obj._frozen)
        self.assertEqual(obj.value, 99)

        with self.assertRaises(ValueError):
            obj.value = 100


class PtrTest(unittest.TestCase):
    """Pointer operations."""

    def test_try_unwrap_null_pointer(self):
        """ptr.try_unwrap() should not crash with TypeError."""
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = b""
        memory += (42).to_bytes(4, "little")
        memory += (0).to_bytes(8, "little")

        test = test_t.from_bytes(memory)
        result = test.p.try_unwrap()
        # Address 0 is valid in our byte buffer, so it may or may not return None
        # The important thing is that it doesn't crash

    def test_try_unwrap_valid_pointer(self):
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = b""
        memory += (42).to_bytes(4, "little")
        memory += (0).to_bytes(8, "little")  # points to self

        test = test_t.from_bytes(memory)
        result = test.p.try_unwrap()
        self.assertIsNotNone(result)
        self.assertEqual(result.a.value, 42)

    def test_ptr_to_str(self):
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = b""
        memory += (1).to_bytes(4, "little")
        memory += (0).to_bytes(8, "little")

        test = test_t.from_bytes(memory)
        s = str(test.p)
        self.assertIn("0x0", s)


class FloatTest(unittest.TestCase):
    """c_float and c_double types."""

    def test_c_float_read(self):
        memory = pystruct.pack("<f", 3.14)
        obj = c_float.from_bytes(memory)
        self.assertAlmostEqual(obj.value, 3.14, places=5)

    def test_c_double_read(self):
        memory = pystruct.pack("<d", 2.718281828)
        obj = c_double.from_bytes(memory)
        self.assertAlmostEqual(obj.value, 2.718281828, places=8)

    def test_c_float_write(self):
        memory = bytearray(4)
        lib = inflater(memory)
        obj = lib.inflate(c_float, 0)

        obj.value = 1.5
        self.assertAlmostEqual(obj.value, 1.5)
        self.assertEqual(memory, pystruct.pack("<f", 1.5))

    def test_c_float_to_bytes_round_trip(self):
        original = pystruct.pack("<f", -42.5)
        obj = c_float.from_bytes(original)
        self.assertEqual(obj.to_bytes(), original)

    def test_c_double_to_bytes_round_trip(self):
        original = pystruct.pack("<d", 123456.789)
        obj = c_double.from_bytes(original)
        self.assertEqual(obj.to_bytes(), original)

    def test_c_float_in_struct(self):
        class test_t(struct):
            x: c_float
            y: c_float

        memory = pystruct.pack("<ff", 1.0, 2.0)
        test = test_t.from_bytes(memory)
        self.assertAlmostEqual(test.x.value, 1.0)
        self.assertAlmostEqual(test.y.value, 2.0)

    def test_c_float_size(self):
        self.assertEqual(c_float.size, 4)

    def test_c_double_size(self):
        self.assertEqual(c_double.size, 8)

    def test_c_float_special_values(self):
        for val in [0.0, float("inf"), float("-inf")]:
            memory = pystruct.pack("<f", val)
            obj = c_float.from_bytes(memory)
            self.assertEqual(obj.value, val)

        # NaN
        memory = pystruct.pack("<f", float("nan"))
        obj = c_float.from_bytes(memory)
        self.assertTrue(math.isnan(obj.value))

    def test_c_float_freeze(self):
        memory = bytearray(pystruct.pack("<f", 9.5))
        lib = inflater(memory)
        obj = lib.inflate(c_float, 0)

        obj.freeze()
        self.assertAlmostEqual(obj.value, 9.5)

        with self.assertRaises(ValueError):
            obj.value = 1.0

    def test_c_float_dunder(self):
        memory = pystruct.pack("<f", 3.14)
        obj = c_float.from_bytes(memory)
        self.assertAlmostEqual(float(obj), 3.14, places=5)


class CStrTest(unittest.TestCase):
    """c_str indexing, iteration, and mutation."""

    def test_get_single_char(self):
        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        self.assertEqual(s.get(0), b"H")
        self.assertEqual(s.get(1), b"e")
        self.assertEqual(s.get(4), b"o")

    def test_iterate_string(self):
        memory = bytearray(b"ABC\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        chars = list(s)
        self.assertEqual(chars, [b"A", b"B", b"C"])

    def test_len(self):
        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        self.assertEqual(len(s), 5)

    def test_getitem(self):
        memory = bytearray(b"XYZ\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        self.assertEqual(s[0], b"X")
        self.assertEqual(s[1], b"Y")
        self.assertEqual(s[2], b"Z")

    def test_index_out_of_range(self):
        memory = bytearray(b"Hi\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        with self.assertRaises(IndexError):
            s.get(100)

    def test_setitem(self):
        """c_str.__setitem__ should not raise TypeError."""
        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        s[0] = b"J"
        self.assertEqual(s.get(0), b"J")

    def test_setitem_middle(self):
        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        s[1] = b"a"
        self.assertEqual(s.get(1), b"a")


if __name__ == "__main__":
    unittest.main()
