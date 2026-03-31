#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import ctypes
import math
import struct as pystruct
import unittest

from libdestruct import (
    c_char, c_double, c_float, c_int, c_long, c_short,
    c_str, c_uchar, c_uint, c_ulong, c_ushort,
    inflater, struct, ptr, ptr_to_self, size_of, array_of,
)
from libdestruct.backing.memory_resolver import MemoryResolver


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

    def test_c_char_from_bytes(self):
        data = (65).to_bytes(1, "little")
        obj = c_char.from_bytes(data)
        self.assertEqual(obj.value, 65)

    def test_c_uchar_from_bytes(self):
        data = (200).to_bytes(1, "little")
        obj = c_uchar.from_bytes(data)
        self.assertEqual(obj.value, 200)

    def test_c_short_from_bytes(self):
        data = (-1234).to_bytes(2, "little", signed=True)
        obj = c_short.from_bytes(data)
        self.assertEqual(obj.value, -1234)

    def test_c_ushort_from_bytes(self):
        data = (60000).to_bytes(2, "little")
        obj = c_ushort.from_bytes(data)
        self.assertEqual(obj.value, 60000)

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

    def test_ptr_add(self):
        """ptr + 1 returns new ptr at addr + size_of(target)."""
        # Array of 3 c_int values: [10, 20, 30]
        memory = bytearray(8 + 12)
        memory[0:8] = (8).to_bytes(8, "little")  # pointer to offset 8
        memory[8:12] = (10).to_bytes(4, "little")
        memory[12:16] = (20).to_bytes(4, "little")
        memory[16:20] = (30).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)

        p2 = p + 1
        self.assertEqual(p2.unwrap().value, 20)

        p3 = p + 2
        self.assertEqual(p3.unwrap().value, 30)

    def test_ptr_sub(self):
        """ptr - 1 returns new ptr at addr - size_of(target)."""
        memory = bytearray(8 + 12)
        memory[0:8] = (12).to_bytes(8, "little")  # pointer to second element
        memory[8:12] = (10).to_bytes(4, "little")
        memory[12:16] = (20).to_bytes(4, "little")
        memory[16:20] = (30).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)

        p2 = p - 1
        self.assertEqual(p2.unwrap().value, 10)

    def test_ptr_add_raw(self):
        """Untyped ptr: ptr + n advances by n bytes."""
        memory = bytearray(8 + 4)
        memory[0:8] = (8).to_bytes(8, "little")  # pointer to offset 8
        memory[8:12] = (0x44332211).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0))
        # No wrapper set, so element size is 1 byte

        p2 = p + 2
        self.assertEqual(p2.get(), 10)  # 8 + 2

    def test_ptr_getitem(self):
        """ptr[0] == unwrap(), ptr[1] == (ptr+1).unwrap()."""
        memory = bytearray(8 + 12)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8:12] = (100).to_bytes(4, "little")
        memory[12:16] = (200).to_bytes(4, "little")
        memory[16:20] = (300).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)

        self.assertEqual(p[0].value, 100)
        self.assertEqual(p[1].value, 200)
        self.assertEqual(p[2].value, 300)

    def test_ptr_arithmetic_chain(self):
        """(ptr + 2)[0] accesses element at index 2."""
        memory = bytearray(8 + 12)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8:12] = (1).to_bytes(4, "little")
        memory[12:16] = (2).to_bytes(4, "little")
        memory[16:20] = (3).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)

        self.assertEqual((p + 2)[0].value, 3)

    def test_unwrap_cached(self):
        """Two unwrap() calls return the same object."""
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = bytearray(12)
        memory[0:4] = (42).to_bytes(4, "little")
        memory[4:12] = (0).to_bytes(8, "little")

        lib = inflater(memory)
        test = lib.inflate(test_t, 0)

        r1 = test.p.unwrap()
        r2 = test.p.unwrap()
        self.assertIs(r1, r2)

    def test_invalidate_clears_cache(self):
        """invalidate() causes next unwrap() to return a new object."""
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = bytearray(12)
        memory[0:4] = (42).to_bytes(4, "little")
        memory[4:12] = (0).to_bytes(8, "little")

        lib = inflater(memory)
        test = lib.inflate(test_t, 0)

        r1 = test.p.unwrap()
        test.p.invalidate()
        r2 = test.p.unwrap()
        self.assertIsNot(r1, r2)

    def test_cache_reflects_memory_change(self):
        """After memory change + invalidate, unwrap gets new value."""
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = bytearray(12)
        memory[0:4] = (42).to_bytes(4, "little")
        memory[4:12] = (0).to_bytes(8, "little")

        lib = inflater(memory)
        test = lib.inflate(test_t, 0)

        self.assertEqual(test.p.unwrap().a.value, 42)
        memory[0:4] = (99).to_bytes(4, "little")
        test.p.invalidate()
        self.assertEqual(test.p.unwrap().a.value, 99)

    def test_try_unwrap_cached(self):
        """try_unwrap() also uses cache."""
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = bytearray(12)
        memory[0:4] = (42).to_bytes(4, "little")
        memory[4:12] = (0).to_bytes(8, "little")

        lib = inflater(memory)
        test = lib.inflate(test_t, 0)

        r1 = test.p.try_unwrap()
        r2 = test.p.try_unwrap()
        self.assertIs(r1, r2)

    def test_cache_invalidated_on_set(self):
        """ptr.value = new_addr auto-invalidates the cache."""
        memory = bytearray(8 + 8)  # ptr + two c_int slots
        memory[0:8] = (8).to_bytes(8, "little")   # points to offset 8
        memory[8:12] = (10).to_bytes(4, "little")
        memory[12:16] = (20).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)

        self.assertEqual(p.unwrap().value, 10)
        p.value = 12  # now points to offset 12
        self.assertEqual(p.unwrap().value, 20)


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


class SizeofTest(unittest.TestCase):
    """size_of() function."""

    def test_size_of_c_int(self):
        self.assertEqual(size_of(c_int), 4)

    def test_size_of_c_long(self):
        self.assertEqual(size_of(c_long), 8)

    def test_size_of_c_float(self):
        self.assertEqual(size_of(c_float), 4)

    def test_size_of_ptr(self):
        self.assertEqual(size_of(ptr), 8)

    def test_size_of_struct(self):
        class two_ints(struct):
            a: c_int
            b: c_int

        self.assertEqual(size_of(two_ints), 8)

    def test_size_of_instance(self):
        obj = c_int.from_bytes((42).to_bytes(4, "little"))
        self.assertEqual(size_of(obj), 4)

    def test_size_of_array_field(self):
        self.assertEqual(size_of(array_of(c_int, 10)), 40)

    def test_size_of_nested_struct(self):
        class inner(struct):
            x: c_int

        class outer(struct):
            a: inner
            b: c_int

        self.assertEqual(size_of(outer), 8)


class HexdumpTest(unittest.TestCase):
    """Pretty hex dump."""

    def test_hexdump_primitive(self):
        data = (0x2a).to_bytes(4, "little")
        obj = c_int.from_bytes(data)
        result = obj.hexdump()
        self.assertIn("2a 00 00 00", result)

    def test_hexdump_struct(self):
        class test_t(struct):
            a: c_int
            b: c_int

        memory = b""
        memory += (1).to_bytes(4, "little")
        memory += (2).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        result = test.hexdump()
        # Should contain field name annotations
        self.assertIn("a", result)
        self.assertIn("b", result)

    def test_hexdump_returns_string(self):
        obj = c_int.from_bytes((0).to_bytes(4, "little"))
        self.assertIsInstance(obj.hexdump(), str)

    def test_hexdump_offset_column(self):
        obj = c_int.from_bytes((0).to_bytes(4, "little"))
        result = obj.hexdump()
        self.assertIn("00000000", result)

    def test_hexdump_ascii_column(self):
        memory = bytearray(b"ABCD")
        lib = inflater(memory)
        obj = lib.inflate(c_int, 0)
        result = obj.hexdump()
        self.assertIn("ABCD", result)

    def test_hexdump_multiline(self):
        """More than 16 bytes should produce multiple lines."""
        class big_t(struct):
            a: c_long
            b: c_long
            c: c_long

        memory = b"\x00" * 24
        test = big_t.from_bytes(memory)
        result = test.hexdump()
        lines = [l for l in result.strip().split("\n") if l.strip()]
        self.assertGreater(len(lines), 1)


class ComparisonTest(unittest.TestCase):
    """Comparison operators on primitive types."""

    def test_int_gt_python_int(self):
        x = c_int.from_bytes((10).to_bytes(4, "little"))
        self.assertTrue(x > 5)
        self.assertFalse(x > 10)

    def test_int_lt_python_int(self):
        x = c_int.from_bytes((3).to_bytes(4, "little"))
        self.assertTrue(x < 5)
        self.assertFalse(x < 3)

    def test_int_ge_le(self):
        x = c_int.from_bytes((7).to_bytes(4, "little"))
        self.assertTrue(x >= 7)
        self.assertTrue(x >= 6)
        self.assertFalse(x >= 8)
        self.assertTrue(x <= 7)
        self.assertTrue(x <= 8)
        self.assertFalse(x <= 6)

    def test_int_eq_python_int(self):
        x = c_int.from_bytes((42).to_bytes(4, "little"))
        self.assertTrue(x == 42)
        self.assertFalse(x == 43)

    def test_int_ne_python_int(self):
        x = c_int.from_bytes((42).to_bytes(4, "little"))
        self.assertTrue(x != 43)
        self.assertFalse(x != 42)

    def test_float_gt_python_float(self):
        x = c_float.from_bytes(pystruct.pack("<f", 3.14))
        self.assertTrue(x > 3.0)
        self.assertFalse(x > 4.0)

    def test_float_eq_python_float(self):
        x = c_double.from_bytes(pystruct.pack("<d", 2.5))
        self.assertTrue(x == 2.5)
        self.assertFalse(x == 2.6)

    def test_obj_vs_obj(self):
        a = c_int.from_bytes((10).to_bytes(4, "little"))
        b = c_int.from_bytes((20).to_bytes(4, "little"))
        self.assertTrue(a < b)
        self.assertTrue(b > a)
        self.assertTrue(a != b)
        self.assertFalse(a == b)

    def test_comparison_returns_not_implemented_for_incompatible(self):
        x = c_int.from_bytes((1).to_bytes(4, "little"))
        self.assertFalse(x == "hello")
        self.assertTrue(x != "hello")


if __name__ == "__main__":
    unittest.main()
