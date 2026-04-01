#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import json
import struct as pystruct
import unittest
from enum import IntEnum

from libdestruct import (
    array_of,
    c_float,
    c_int,
    c_long,
    c_str,
    enum_of,
    inflater,
    ptr_to,
    struct,
)
from libdestruct.common.enum import enum
from libdestruct.common.union import tagged_union, union, union_of


class ToDictTest(unittest.TestCase):
    def test_primitive_to_dict(self):
        """Primitive to_dict returns its Python value."""
        x = c_int.from_bytes(b"\x2a\x00\x00\x00")
        self.assertEqual(x.to_dict(), 42)

    def test_struct_to_dict(self):
        """Struct to_dict returns a dict of field names to values."""
        class point_t(struct):
            x: c_int
            y: c_int

        memory = pystruct.pack("<ii", 10, 20)
        point = point_t.from_bytes(memory)
        result = point.to_dict()
        self.assertEqual(result, {"x": 10, "y": 20})

    def test_nested_struct_to_dict(self):
        """Nested struct produces nested dicts."""
        class vec2(struct):
            x: c_int
            y: c_int

        class entity_t(struct):
            id: c_int
            pos: vec2

        memory = pystruct.pack("<iii", 1, 10, 20)
        entity = entity_t.from_bytes(memory)
        result = entity.to_dict()
        self.assertEqual(result, {"id": 1, "pos": {"x": 10, "y": 20}})

    def test_struct_with_long_to_dict(self):
        """Integer field returns its value."""
        class data_t(struct):
            value: c_int
            ref: c_long

        memory = pystruct.pack("<iq", 42, 0x1000)
        data = data_t.from_bytes(memory)
        result = data.to_dict()
        self.assertEqual(result, {"value": 42, "ref": 0x1000})

    def test_struct_with_enum_to_dict(self):
        """Enum field returns its integer value."""
        class Color(IntEnum):
            RED = 0
            GREEN = 1
            BLUE = 2

        class pixel_t(struct):
            color: enum = enum_of(Color)
            alpha: c_int

        memory = pystruct.pack("<ii", 1, 255)
        pixel = pixel_t.from_bytes(memory)
        result = pixel.to_dict()
        self.assertEqual(result["color"], 1)
        self.assertEqual(result["alpha"], 255)

    def test_struct_with_array_to_dict(self):
        """Array field returns a list of values."""
        class packet_t(struct):
            data: c_int = array_of(c_int, 3)

        memory = pystruct.pack("<iii", 10, 20, 30)
        pkt = packet_t.from_bytes(memory)
        result = pkt.to_dict()
        self.assertEqual(result, {"data": [10, 20, 30]})

    def test_struct_with_tagged_union_to_dict(self):
        """Tagged union returns the active variant's value."""
        class msg_t(struct):
            type: c_int
            payload: union = tagged_union("type", {0: c_int, 1: c_float})

        memory = pystruct.pack("<ii", 0, 42)
        msg = msg_t.from_bytes(memory)
        result = msg.to_dict()
        self.assertEqual(result["type"], 0)
        self.assertEqual(result["payload"], 42)

    def test_struct_with_plain_union_to_dict(self):
        """Plain union returns a dict of all variant values."""
        class packet_t(struct):
            data: union = union_of({"i": c_int, "f": c_float})

        memory = pystruct.pack("<i", 42)
        pkt = packet_t.from_bytes(memory)
        result = pkt.to_dict()
        self.assertIn("i", result["data"])
        self.assertIn("f", result["data"])
        self.assertEqual(result["data"]["i"], 42)

    def test_to_dict_is_json_serializable(self):
        """to_dict output can be passed to json.dumps."""
        class point_t(struct):
            x: c_int
            y: c_int

        memory = pystruct.pack("<ii", 10, 20)
        point = point_t.from_bytes(memory)
        result = json.dumps(point.to_dict())
        self.assertEqual(json.loads(result), {"x": 10, "y": 20})

    def test_float_to_dict(self):
        """Float to_dict returns its Python float value."""
        f = c_float.from_bytes(pystruct.pack("<f", 3.14))
        self.assertAlmostEqual(f.to_dict(), 3.14, places=2)
