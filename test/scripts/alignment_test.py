#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest

from libdestruct import c_char, c_int, c_long, c_short, c_uchar, inflater, offset, size_of, struct
from libdestruct.common.utils import alignment_of


class AlignmentOfTest(unittest.TestCase):
    def test_alignment_of_c_char(self):
        self.assertEqual(alignment_of(c_char), 1)

    def test_alignment_of_c_short(self):
        self.assertEqual(alignment_of(c_short), 2)

    def test_alignment_of_c_int(self):
        self.assertEqual(alignment_of(c_int), 4)

    def test_alignment_of_c_long(self):
        self.assertEqual(alignment_of(c_long), 8)


class AlignedStructTest(unittest.TestCase):
    def test_packed_struct_no_padding(self):
        """Default structs are packed with no alignment padding."""
        class packed_t(struct):
            a: c_char
            b: c_int

        # packed: 1 + 4 = 5
        self.assertEqual(size_of(packed_t), 5)

    def test_aligned_struct_padding(self):
        """Aligned struct inserts padding for field alignment."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        # aligned: 1 + 3 padding + 4 = 8
        self.assertEqual(size_of(aligned_t), 8)

    def test_aligned_struct_tail_padding(self):
        """Aligned struct pads total size to max alignment."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_int
            b: c_char

        # aligned: 4 + 1 + 3 tail padding = 8 (aligned to 4-byte boundary)
        self.assertEqual(size_of(aligned_t), 8)

    def test_aligned_struct_read_values(self):
        """Values are read correctly from aligned positions."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        # a at offset 0, padding 3 bytes, b at offset 4
        memory = pystruct.pack("<b", 0x41) + b"\x00" * 3 + pystruct.pack("<i", 42)
        s = aligned_t.from_bytes(memory)
        self.assertEqual(s.a.value, 0x41)
        self.assertEqual(s.b.value, 42)

    def test_aligned_struct_mixed_types(self):
        """Correct alignment for mixed type sizes."""
        class mixed_t(struct):
            _aligned_ = True
            a: c_char       # offset 0, size 1
            b: c_short      # offset 2 (aligned to 2), size 2
            c: c_char       # offset 4, size 1
            d: c_int        # offset 8 (aligned to 4), size 4
            e: c_char       # offset 12, size 1
            f: c_long       # offset 16 (aligned to 8), size 8

        # total: 24 (padded to 8-byte boundary)
        self.assertEqual(size_of(mixed_t), 24)

    def test_aligned_struct_write(self):
        """Writing to aligned struct fields works correctly."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        memory = bytearray(8)
        lib = inflater(memory)
        s = lib.inflate(aligned_t, 0)
        s.a.value = 0x41
        s.b.value = 42
        self.assertEqual(s.a.value, 0x41)
        self.assertEqual(s.b.value, 42)

    def test_aligned_nested_struct(self):
        """Nested aligned struct respects inner struct alignment."""
        class inner_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        class outer_t(struct):
            _aligned_ = True
            x: c_char
            inner: inner_t

        # inner_t: size 8, alignment 4
        # outer_t: x at 0 (1 byte), inner at 4 (aligned to 4), inner is 8 bytes
        # total: 12, padded to 4-byte boundary = 12
        self.assertEqual(size_of(outer_t), 12)

    def test_aligned_struct_all_same_size(self):
        """Aligned struct with uniform field sizes has no extra padding."""
        class uniform_t(struct):
            _aligned_ = True
            a: c_int
            b: c_int
            c: c_int

        # No padding needed: 4 + 4 + 4 = 12, tail padded to 4 = 12
        self.assertEqual(size_of(uniform_t), 12)

    def test_alignment_of_aligned_struct(self):
        """alignment_of returns the struct's computed alignment."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        self.assertEqual(alignment_of(aligned_t), 4)

    def test_alignment_of_packed_struct(self):
        """Packed struct has alignment 1."""
        class packed_t(struct):
            a: c_char
            b: c_int

        self.assertEqual(alignment_of(packed_t), 1)


class CustomAlignmentTest(unittest.TestCase):
    def test_aligned_integer_width(self):
        """_aligned_ = N uses N as the struct's minimum alignment."""
        class wide_t(struct):
            _aligned_ = 16
            a: c_int

        # 4 bytes data, padded to 16-byte boundary
        self.assertEqual(size_of(wide_t), 16)
        self.assertEqual(alignment_of(wide_t), 16)

    def test_aligned_32(self):
        """_aligned_ = 32 pads to 32-byte boundary."""
        class wide_t(struct):
            _aligned_ = 32
            a: c_char
            b: c_int

        # 1 + 3 padding + 4 = 8 data, padded to 32
        self.assertEqual(size_of(wide_t), 32)

    def test_aligned_true_same_as_natural(self):
        """_aligned_ = True uses natural alignment (max 8)."""
        class a_t(struct):
            _aligned_ = True
            x: c_char
            y: c_long

        class b_t(struct):
            _aligned_ = 8
            x: c_char
            y: c_long

        self.assertEqual(size_of(a_t), size_of(b_t))
        self.assertEqual(alignment_of(a_t), alignment_of(b_t))


class AlignmentWithOffsetTest(unittest.TestCase):
    def test_explicit_offset_overrides_alignment(self):
        """Explicit offset is respected even if it's not naturally aligned."""
        class s_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int = offset(3)

        # b should be at offset 3, not rounded up to 4
        self.assertEqual(size_of(s_t), 7)  # 3 + 4

    def test_explicit_offset_read_values(self):
        """Values at explicit offsets in aligned structs are read correctly."""
        class s_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int = offset(3)

        memory = pystruct.pack("<b", 0x41) + b"\x00\x00" + pystruct.pack("<i", 42)
        s = s_t.from_bytes(memory)
        self.assertEqual(s.a.value, 0x41)
        self.assertEqual(s.b.value, 42)

    def test_alignment_resumes_after_explicit_offset(self):
        """Alignment padding resumes for fields after an explicitly-offset field."""
        class s_t(struct):
            _aligned_ = True
            a: c_int = offset(0)
            b: c_char = offset(4)
            c: c_int  # should be at offset 8 (aligned to 4)

        self.assertEqual(size_of(s_t), 12)  # 4 + 1 + 3 padding + 4
