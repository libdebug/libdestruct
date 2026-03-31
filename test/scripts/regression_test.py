#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import ctypes
import unittest
from enum import IntEnum

from libdestruct import c_int, c_long, c_str, c_uint, inflater, struct, ptr, ptr_to_self, array_of, enum, enum_of
from libdestruct.backing.fake_resolver import FakeResolver


class FakeResolverTest(unittest.TestCase):
    """Issue #1: FakeResolver.resolve() uses wrong default page size for non-zero offset."""

    def test_resolve_default_page_with_offset(self):
        resolver = FakeResolver()
        resolver.address = 0x800  # offset 0x800 within page 0

        # Reading from an address with a non-zero page offset in a non-existent page
        # should return zero bytes, not empty bytes
        data = resolver.resolve(4, 0)
        self.assertEqual(len(data), 4)
        self.assertEqual(data, b"\x00\x00\x00\x00")


class PtrTryUnwrapTest(unittest.TestCase):
    """Issue #2: ptr.try_unwrap() passes wrong number of args to resolve()."""

    def test_try_unwrap_null_pointer(self):
        class test_t(struct):
            a: c_int
            p: ptr = ptr_to_self()

        memory = b""
        memory += (42).to_bytes(4, "little")
        memory += (0).to_bytes(8, "little")

        test = test_t.from_bytes(memory)
        # try_unwrap on a null pointer should return None, not crash with TypeError
        result = test.p.try_unwrap()
        # Address 0 is valid in our byte buffer, so it may or may not return None
        # The important thing is that it doesn't crash


class CStrGetTest(unittest.TestCase):
    """Issue #3: c_str.get(index) passes wrong number of args to resolve()."""

    def test_get_single_char(self):
        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        self.assertEqual(s.get(0), b"H")
        self.assertEqual(s.get(1), b"e")
        self.assertEqual(s.get(4), b"o")


class CtypesGenericFrozenTest(unittest.TestCase):
    """Issue #4: _ctypes_generic.to_bytes() when frozen returns garbage via bytes(int)."""

    def test_frozen_to_bytes(self):
        memory = (42).to_bytes(ctypes.sizeof(ctypes.c_int), "little")
        lib = inflater(memory)
        obj = lib.inflate(ctypes.c_int, 0)

        self.assertEqual(obj.value, 42)
        obj.freeze()
        self.assertEqual(obj.value, 42)
        # bytes(42) produces b'\x00'*42, not the 4-byte LE representation
        self.assertEqual(len(obj.to_bytes()), ctypes.sizeof(ctypes.c_int))
        self.assertEqual(obj.to_bytes(), memory)


class ObjFromBytesTest(unittest.TestCase):
    """Issue #5: obj.from_bytes() is broken for non-struct types like c_int."""

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


class ArrayValueTest(unittest.TestCase):
    """Issue #6: array.get() signature is incompatible with obj.get(), breaking .value property."""

    def test_array_value_property(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(5))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 5), 0)

        # .value calls self.get() without args - should not raise TypeError
        val = arr.value
        self.assertIsNotNone(val)

    def test_array_repr(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(3))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)

        # __repr__ calls self.get() - should not crash
        r = repr(arr)
        self.assertIsInstance(r, str)


class StructMemberCollisionTest(unittest.TestCase):
    """Issue #7: struct field named 'value' or 'address' crashes during inflation."""

    def test_struct_with_value_field(self):
        class test_t(struct):
            value: c_int

        memory = (42).to_bytes(4, "little")
        # Should not raise RuntimeError from obj.value setter
        test = test_t.from_bytes(memory)
        self.assertEqual(test.value.value, 42)

    def test_struct_with_address_field(self):
        class test_t(struct):
            address: c_int
            b: c_int

        memory = b""
        memory += (10).to_bytes(4, "little")
        memory += (20).to_bytes(4, "little")

        # Should not raise AttributeError from read-only property
        test = test_t.from_bytes(memory)
        self.assertEqual(test.address.value, 10)
        self.assertEqual(test.b.value, 20)


class CStrSetItemTest(unittest.TestCase):
    """Issue #8: c_str.__setitem__ calls obj.set(index, value) which has wrong arity."""

    def test_setitem(self):
        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)

        # Should not raise TypeError
        s[0] = b"J"
        self.assertEqual(s.get(0), b"J")


class EnumToStrTest(unittest.TestCase):
    """Issue #11: enum.to_str() adds unexpected leading indentation."""

    def test_enum_in_struct_to_str(self):
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


class StructParserTest(unittest.TestCase):
    """Issue #16: struct_parser doesn't handle double pointers (int **pp)."""

    def test_double_pointer(self):
        from libdestruct.c.struct_parser import definition_to_type

        # Should not raise TypeError: "Definition must be a type declaration."
        struct_type = definition_to_type("struct test { int **pp; };")
        self.assertIn("pp", struct_type.__annotations__)


class BytearrayMemoryBytesTest(unittest.TestCase):
    """Issue #6: __bytes__ fails on Python 3.13+ when backing memory is bytearray."""

    def test_resolve_returns_bytes(self):
        from libdestruct.backing.memory_resolver import MemoryResolver

        # MemoryResolver.resolve() should always return bytes, even when
        # the backing memory is a bytearray
        resolver = MemoryResolver(bytearray(b"\x01\x02\x03\x04"), 0)
        result = resolver.resolve(4, 0)
        self.assertIsInstance(result, bytes)

    def test_bytes_on_bytearray_backed_c_int(self):
        lib = inflater(bytearray(b"\x2a\x00\x00\x00"))
        obj = lib.inflate(c_int, 0)

        result = bytes(obj)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 4)

    def test_bytes_on_bytearray_backed_c_str(self):
        lib = inflater(bytearray(b"Hello\x00"))
        s = lib.inflate(c_str, 0)

        result = bytes(s)
        self.assertIsInstance(result, bytes)

    def test_bytes_on_bytearray_backed_ptr(self):
        class test_t(struct):
            p: ptr = ptr_to_self()

        memory = bytearray(b"\x00" * 8)
        test = test_t.from_bytes(memory)

        result = test.p.to_bytes()
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 8)

    def test_c_str_get_returns_bytes(self):
        lib = inflater(bytearray(b"Hello\x00"))
        s = lib.inflate(c_str, 0)

        # get() without index returns the full string
        result = s.get()
        self.assertIsInstance(result, bytes)

        # get() with index returns a single byte
        result = s.get(0)
        self.assertIsInstance(result, bytes)


if __name__ == "__main__":
    unittest.main()
