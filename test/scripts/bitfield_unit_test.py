#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdestruct import c_int, c_uint, c_long, inflater, struct, bitfield_of
from libdestruct.c.struct_parser import definition_to_type


class BitfieldReadTest(unittest.TestCase):
    """Bitfield read operations."""

    def test_single_bitfield_read(self):
        class test_t(struct):
            flags: c_uint = bitfield_of(c_uint, 3)

        # 0b00000101 = 5, low 3 bits = 5
        memory = (0b00000101).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.flags.value, 5)

    def test_multiple_bitfields_packing(self):
        class test_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)
            b: c_uint = bitfield_of(c_uint, 5)

        # a uses bits 0-2, b uses bits 3-7
        # a=5 (0b101), b=10 (0b01010) -> combined: 0b01010_101 = 0x55
        memory = (0b01010_101).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.a.value, 5)
        self.assertEqual(test.b.value, 10)

        # Struct should be 4 bytes total (both share one c_uint)
        self.assertEqual(test.to_bytes(), memory)

    def test_bitfield_signed(self):
        class test_t(struct):
            val: c_int = bitfield_of(c_int, 4)

        # 4-bit signed: 0b1111 = -1
        memory = (0b1111).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.val.value, -1)

        # 4-bit signed: 0b0111 = 7
        memory2 = (0b0111).to_bytes(4, "little")
        test2 = test_t.from_bytes(memory2)
        self.assertEqual(test2.val.value, 7)

    def test_bitfield_full_width(self):
        class test_t(struct):
            val: c_uint = bitfield_of(c_uint, 32)

        memory = (0xDEADBEEF).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.val.value, 0xDEADBEEF)


class BitfieldWriteTest(unittest.TestCase):
    """Bitfield write operations."""

    def test_bitfield_write(self):
        class test_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)
            b: c_uint = bitfield_of(c_uint, 5)

        memory = bytearray(4)
        from libdestruct import inflater
        lib = inflater(memory)
        test = lib.inflate(test_t, 0)

        test.a.value = 7   # 0b111
        test.b.value = 15  # 0b01111

        self.assertEqual(test.a.value, 7)
        self.assertEqual(test.b.value, 15)

        # Verify only relevant bits changed
        raw = int.from_bytes(memory[:4], "little")
        self.assertEqual(raw & 0b111, 7)          # bits 0-2
        self.assertEqual((raw >> 3) & 0b11111, 15)  # bits 3-7


class BitfieldRoundTripTest(unittest.TestCase):
    """Bitfield serialization."""

    def test_bitfield_round_trip(self):
        class test_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)
            b: c_uint = bitfield_of(c_uint, 5)
            c: c_int

        # a=3, b=10, c=42
        # a=0b011, b=0b01010 -> byte 0-3: 0b01010_011 = 0x53
        val = 0b01010_011
        memory = val.to_bytes(4, "little") + (42).to_bytes(4, "little")

        test = test_t.from_bytes(memory)
        self.assertEqual(test.a.value, 3)
        self.assertEqual(test.b.value, 10)
        self.assertEqual(test.c.value, 42)

        self.assertEqual(test.to_bytes(), memory)


class BitfieldBackingTypeTest(unittest.TestCase):
    """Bitfield backing type transitions."""

    def test_bitfield_backing_type_change(self):
        class test_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)
            b: c_uint = bitfield_of(c_uint, 5)
            # Different backing type -> new group
            c: c_long = bitfield_of(c_long, 16)

        # a+b share 4 bytes (c_uint), c uses 8 bytes (c_long)
        # Total = 12 bytes
        memory = b"\x00" * 12
        test = test_t.from_bytes(memory)
        self.assertEqual(len(test.to_bytes()), 12)


class BitfieldCParserTest(unittest.TestCase):
    """C parser bitfield support."""

    def test_bitfield_c_parser(self):
        t = definition_to_type("struct test { unsigned int flags:3; unsigned int reserved:5; };")
        self.assertIn("flags", t.__annotations__)
        self.assertIn("reserved", t.__annotations__)

        # Inflate and verify
        memory = (0b01010_101).to_bytes(4, "little")
        test = t.from_bytes(memory)
        self.assertEqual(test.flags.value, 5)
        self.assertEqual(test.reserved.value, 10)


class BitfieldFreezeTest(unittest.TestCase):
    def test_bitfield_freeze_to_bytes(self):
        """Frozen bitfield struct to_bytes returns original bytes."""
        memory = bytearray(4)
        memory[0] = 0b_00101_011  # a=3, b=5

        class flags_t(struct):
            a: c_int = bitfield_of(c_int, 3)
            b: c_int = bitfield_of(c_int, 5)

        lib = inflater(memory)
        s = lib.inflate(flags_t, 0)
        original_bytes = bytes(s.to_bytes())
        s.freeze()
        memory[0] = 0xFF
        self.assertEqual(s.to_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()
