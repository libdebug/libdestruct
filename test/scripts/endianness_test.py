#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest

from libdestruct import (
    array_of,
    bitfield_of,
    c_char,
    c_double,
    c_float,
    c_int,
    c_long,
    c_short,
    c_uint,
    c_ulong,
    c_ushort,
    inflater,
    ptr,
    ptr_to,
    size_of,
    struct,
)
from libdestruct.backing.memory_resolver import MemoryResolver


class BigEndianIntegerTest(unittest.TestCase):
    def test_c_int_read_big_endian(self):
        """Big-endian c_int reads bytes in big-endian order."""
        memory = bytearray(pystruct.pack(">i", 0x12345678))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_int, 0)
        self.assertEqual(val.value, 0x12345678)

    def test_c_int_read_little_endian_default(self):
        """Default endianness is little-endian (backward compatibility)."""
        memory = bytearray(pystruct.pack("<i", 0x12345678))
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        self.assertEqual(val.value, 0x12345678)

    def test_c_short_read_big_endian(self):
        """Big-endian c_short reads correctly."""
        memory = bytearray(pystruct.pack(">h", -1234))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_short, 0)
        self.assertEqual(val.value, -1234)

    def test_c_long_read_big_endian(self):
        """Big-endian c_long reads correctly."""
        memory = bytearray(pystruct.pack(">q", 0x0102030405060708))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_long, 0)
        self.assertEqual(val.value, 0x0102030405060708)

    def test_c_uint_read_big_endian(self):
        """Big-endian unsigned int reads correctly."""
        memory = bytearray(pystruct.pack(">I", 0xDEADBEEF))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_uint, 0)
        self.assertEqual(val.value, 0xDEADBEEF)

    def test_c_int_write_big_endian(self):
        """Writing a big-endian c_int stores bytes in big-endian order."""
        memory = bytearray(4)
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_int, 0)
        val.value = 0x12345678
        self.assertEqual(memory, pystruct.pack(">i", 0x12345678))

    def test_c_int_to_bytes_big_endian(self):
        """to_bytes returns big-endian representation."""
        memory = bytearray(pystruct.pack(">i", 42))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_int, 0)
        self.assertEqual(val.to_bytes(), pystruct.pack(">i", 42))


class BigEndianFloatTest(unittest.TestCase):
    def test_c_float_read_big_endian(self):
        """Big-endian c_float reads correctly."""
        memory = bytearray(pystruct.pack(">f", 3.14))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_float, 0)
        self.assertAlmostEqual(val.value, 3.14, places=5)

    def test_c_double_read_big_endian(self):
        """Big-endian c_double reads correctly."""
        memory = bytearray(pystruct.pack(">d", 2.718281828))
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_double, 0)
        self.assertAlmostEqual(val.value, 2.718281828, places=8)

    def test_c_float_write_big_endian(self):
        """Writing a big-endian c_float stores bytes in big-endian order."""
        memory = bytearray(4)
        lib = inflater(memory, endianness="big")
        val = lib.inflate(c_float, 0)
        val.value = 1.5
        self.assertEqual(memory, pystruct.pack(">f", 1.5))


class BigEndianStructTest(unittest.TestCase):
    def test_struct_fields_inherit_endianness(self):
        """Struct fields inherit big-endian from the inflater."""
        class s_t(struct):
            a: c_int
            b: c_short

        memory = bytearray(pystruct.pack(">i", 0x12345678) + pystruct.pack(">h", -100))
        lib = inflater(memory, endianness="big")
        s = lib.inflate(s_t, 0)
        self.assertEqual(s.a.value, 0x12345678)
        self.assertEqual(s.b.value, -100)

    def test_nested_struct_inherits_endianness(self):
        """Nested struct fields also inherit big-endian."""
        class inner_t(struct):
            x: c_int

        class outer_t(struct):
            a: c_short
            inner: inner_t

        memory = bytearray(pystruct.pack(">h", 0x0102) + pystruct.pack(">i", 0x03040506))
        lib = inflater(memory, endianness="big")
        s = lib.inflate(outer_t, 0)
        self.assertEqual(s.a.value, 0x0102)
        self.assertEqual(s.inner.x.value, 0x03040506)

    def test_struct_write_big_endian(self):
        """Writing to struct fields stores bytes in big-endian order."""
        class s_t(struct):
            a: c_int

        memory = bytearray(4)
        lib = inflater(memory, endianness="big")
        s = lib.inflate(s_t, 0)
        s.a.value = 0x1A2B3C4D
        self.assertEqual(memory, b"\x1A\x2B\x3C\x4D")


class BigEndianFromBytesTest(unittest.TestCase):
    def test_from_bytes_big_endian(self):
        """from_bytes with endianness='big' reads correctly."""
        data = pystruct.pack(">i", 0x12345678)
        val = c_int.from_bytes(data, endianness="big")
        self.assertEqual(val.value, 0x12345678)

    def test_from_bytes_default_little_endian(self):
        """from_bytes defaults to little-endian."""
        data = pystruct.pack("<i", 42)
        val = c_int.from_bytes(data)
        self.assertEqual(val.value, 42)

    def test_struct_from_bytes_big_endian(self):
        """Struct from_bytes with big-endian reads all fields correctly."""
        class s_t(struct):
            a: c_int
            b: c_short

        data = pystruct.pack(">i", 1000) + pystruct.pack(">h", 2000)
        s = s_t.from_bytes(data, endianness="big")
        self.assertEqual(s.a.value, 1000)
        self.assertEqual(s.b.value, 2000)


class BigEndianRoundTripTest(unittest.TestCase):
    def test_int_round_trip(self):
        """Big-endian int survives from_bytes -> to_bytes round trip."""
        original = pystruct.pack(">i", 0x12345678)
        val = c_int.from_bytes(original, endianness="big")
        self.assertEqual(val.to_bytes(), original)

    def test_struct_round_trip(self):
        """Big-endian struct survives from_bytes -> to_bytes round trip."""
        class s_t(struct):
            a: c_int
            b: c_short

        original = pystruct.pack(">i", 0x1A2B3C4D) + pystruct.pack(">h", 0x1122)
        s = s_t.from_bytes(original, endianness="big")
        self.assertEqual(s.to_bytes(), original)

    def test_float_round_trip(self):
        """Big-endian float survives from_bytes -> to_bytes round trip."""
        original = pystruct.pack(">f", 3.14)
        val = c_float.from_bytes(original, endianness="big")
        self.assertEqual(val.to_bytes(), original)


class BigEndianPointerTest(unittest.TestCase):
    def test_ptr_read_big_endian(self):
        """Big-endian pointer reads address in big-endian order."""
        memory = bytearray(16)
        # Pointer at offset 0 with big-endian value 8
        memory[0:8] = pystruct.pack(">Q", 8)
        # Target int at offset 8
        memory[8:12] = pystruct.pack(">i", 42)

        lib = inflater(memory, endianness="big")
        p = lib.inflate(ptr_to(c_int), 0)
        self.assertEqual(p.get(), 8)
        self.assertEqual(p.unwrap().value, 42)

    def test_ptr_arithmetic_big_endian(self):
        """Pointer arithmetic works with big-endian pointers."""
        memory = bytearray(24)
        # Pointer at offset 0 pointing to offset 8
        memory[0:8] = pystruct.pack(">Q", 8)
        # Two ints at offset 8 and 12
        memory[8:12] = pystruct.pack(">i", 100)
        memory[12:16] = pystruct.pack(">i", 200)

        lib = inflater(memory, endianness="big")
        p = lib.inflate(ptr_to(c_int), 0)
        self.assertEqual(p[0].value, 100)
        self.assertEqual(p[1].value, 200)


class BigEndianArrayTest(unittest.TestCase):
    def test_array_big_endian(self):
        """Array elements inherit big-endian."""
        class s_t(struct):
            arr: list[c_int] = array_of(c_int, 3)

        data = b""
        for v in [10, 20, 30]:
            data += pystruct.pack(">i", v)

        memory = bytearray(data)
        lib = inflater(memory, endianness="big")
        s = lib.inflate(s_t, 0)
        self.assertEqual(s.arr[0].value, 10)
        self.assertEqual(s.arr[1].value, 20)
        self.assertEqual(s.arr[2].value, 30)


class BigEndianBitfieldTest(unittest.TestCase):
    def test_bitfield_big_endian(self):
        """Bitfield reads from big-endian backing integer."""
        class s_t(struct):
            flags: c_uint = bitfield_of(c_uint, 3)

        # Value 5 (0b101) in big-endian uint32
        memory = bytearray(pystruct.pack(">I", 5))
        lib = inflater(memory, endianness="big")
        s = lib.inflate(s_t, 0)
        self.assertEqual(s.flags.value, 5)

    def test_bitfield_write_big_endian(self):
        """Bitfield writes to big-endian backing integer."""
        class s_t(struct):
            flags: c_uint = bitfield_of(c_uint, 3)

        memory = bytearray(4)
        lib = inflater(memory, endianness="big")
        s = lib.inflate(s_t, 0)
        s.flags.value = 5
        self.assertEqual(memory, pystruct.pack(">I", 5))


if __name__ == "__main__":
    unittest.main()
