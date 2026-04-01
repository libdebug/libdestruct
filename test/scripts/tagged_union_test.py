#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest

from libdestruct import c_float, c_int, c_long, inflater, size_of, struct
from libdestruct.common.union import tagged_union, union, union_of


class TaggedUnionTest(unittest.TestCase):
    def test_basic_variant_selection(self):
        """Union selects the correct variant based on discriminator value."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_float})

        memory = pystruct.pack("<i", 0) + pystruct.pack("<i", 42)
        msg = msg_t.from_bytes(memory)
        self.assertEqual(msg.payload.value, 42)

    def test_different_discriminator_value(self):
        """Different discriminator value selects different variant."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_float})

        memory = pystruct.pack("<i", 1) + pystruct.pack("<f", 3.14)
        msg = msg_t.from_bytes(memory)
        self.assertAlmostEqual(msg.payload.value, 3.14, places=2)

    def test_union_size_is_max_variant(self):
        """Union size equals the max of all variant sizes."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_long})

        # c_int(4) + max(c_int(4), c_long(8)) = 12
        self.assertEqual(size_of(msg_t), 12)

    def test_struct_variant_field_access(self):
        """Struct variant fields are accessible through the union."""
        class point_t(struct):
            x: c_int
            y: c_int

        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: point_t})

        # max(c_int=4, point_t=8) = 8; total = 4 + 8 = 12
        memory = pystruct.pack("<i", 1) + pystruct.pack("<ii", 10, 20)
        msg = msg_t.from_bytes(memory)
        self.assertEqual(msg.payload.x.value, 10)
        self.assertEqual(msg.payload.y.value, 20)

    def test_unknown_discriminator_raises(self):
        """Unknown discriminator value raises ValueError."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int})

        memory = pystruct.pack("<i", 99) + b"\x00" * 4
        with self.assertRaises(ValueError):
            msg_t.from_bytes(memory)

    def test_union_to_bytes_full_size(self):
        """to_bytes returns the full union-sized region, not just the active variant."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_long})

        # 4 bytes type + 4 bytes c_int + 4 bytes padding = 12 bytes total
        data = pystruct.pack("<i", 0) + pystruct.pack("<i", 42) + b"\xaa\xbb\xcc\xdd"
        msg = msg_t.from_bytes(data)
        self.assertEqual(len(msg.payload.to_bytes()), 8)

    def test_union_write(self):
        """Writing to the active variant updates memory."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_float})

        memory = bytearray(8)
        lib = inflater(memory)
        msg = lib.inflate(msg_t, 0)
        msg.payload.value = 100
        self.assertEqual(msg.payload.value, 100)

    def test_variant_property(self):
        """variant property returns the active variant object."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_float})

        memory = pystruct.pack("<i", 0) + pystruct.pack("<i", 42)
        msg = msg_t.from_bytes(memory)
        self.assertIsNotNone(msg.payload.variant)

    def test_struct_total_size_with_union(self):
        """Struct containing a union has correct total size."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_float})
            trailer: c_int

        # c_int(4) + max(c_int(4), c_float(4)) + c_int(4) = 12
        self.assertEqual(size_of(msg_t), 12)


class PlainUnionTest(unittest.TestCase):
    def test_plain_union_read_all_variants(self):
        """Plain union inflates all variants at the same offset."""
        class packet_t(struct):
            data: union = union_of({"i": c_int, "f": c_float})

        memory = pystruct.pack("<f", 3.14)
        pkt = packet_t.from_bytes(memory)
        self.assertAlmostEqual(pkt.data.f.value, 3.14, places=2)
        self.assertIsInstance(pkt.data.i.value, int)

    def test_plain_union_size(self):
        """Plain union size is max of all variant sizes."""
        class packet_t(struct):
            data: union = union_of({"i": c_int, "l": c_long})

        self.assertEqual(size_of(packet_t), 8)

    def test_plain_union_write(self):
        """Writing to a variant of a plain union updates shared memory."""
        class packet_t(struct):
            data: union = union_of({"i": c_int, "f": c_float})

        memory = bytearray(4)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)
        pkt.data.i.value = 42
        self.assertEqual(pkt.data.i.value, 42)

    def test_plain_union_struct_variant(self):
        """Plain union can contain struct variants."""
        class point_t(struct):
            x: c_int
            y: c_int

        class packet_t(struct):
            data: union = union_of({"raw": c_long, "point": point_t})

        memory = pystruct.pack("<ii", 10, 20)
        pkt = packet_t.from_bytes(memory)
        self.assertEqual(pkt.data.point.x.value, 10)
        self.assertEqual(pkt.data.point.y.value, 20)

    def test_plain_union_to_bytes(self):
        """Plain union to_bytes returns max-size region."""
        class packet_t(struct):
            data: union = union_of({"i": c_int, "l": c_long})

        memory = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        pkt = packet_t.from_bytes(memory)
        self.assertEqual(len(pkt.data.to_bytes()), 8)
        self.assertEqual(pkt.data.to_bytes(), memory)

    def test_plain_union_shared_memory(self):
        """All variants of a plain union share the same memory."""
        class packet_t(struct):
            data: union = union_of({"i": c_int, "f": c_float})

        memory = bytearray(4)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)
        pkt.data.i.value = 42
        # Reading as float should reinterpret the same bytes
        expected_float = pystruct.unpack("<f", pystruct.pack("<i", 42))[0]
        self.assertAlmostEqual(pkt.data.f.value, expected_float)
