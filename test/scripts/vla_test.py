#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest

from libdestruct import struct, c_int, c_short, c_long, inflater, size_of
from libdestruct.common.array import array
from libdestruct.common.array.vla_of import vla_of


class VLATest(unittest.TestCase):
    """Variable-length array tests."""

    def test_vla_descriptor_read(self):
        """vla_of(c_int, 'length') reads correct elements."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        # length=3, followed by 3 ints
        data = pystruct.pack("<i", 3) + pystruct.pack("<iii", 10, 20, 30)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(pkt.length.value, 3)
        self.assertEqual(len(pkt.data), 3)
        self.assertEqual(pkt.data[0].value, 10)
        self.assertEqual(pkt.data[1].value, 20)
        self.assertEqual(pkt.data[2].value, 30)

    def test_vla_subscript_read(self):
        """array[c_int, 'length'] subscript syntax."""
        class packet_t(struct):
            length: c_int
            data: array[c_int, "length"]

        data = pystruct.pack("<i", 2) + pystruct.pack("<ii", 42, 99)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(len(pkt.data), 2)
        self.assertEqual(pkt.data[0].value, 42)
        self.assertEqual(pkt.data[1].value, 99)

    def test_vla_zero_length(self):
        """Count == 0, VLA is empty."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<i", 0)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(len(pkt.data), 0)

    def test_vla_class_size(self):
        """size_of(packet_t) returns fixed part only (excludes VLA)."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        self.assertEqual(size_of(packet_t), 4)

    def test_vla_instance_size(self):
        """size_of(instance) includes VLA data."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<i", 3) + pystruct.pack("<iii", 10, 20, 30)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(size_of(pkt), 4 + 3 * 4)

    def test_vla_to_bytes(self):
        """to_bytes() includes fixed + VLA data."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        raw = pystruct.pack("<iiii", 3, 10, 20, 30)
        memory = bytearray(raw)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(pkt.to_bytes(), raw)

    def test_vla_iteration(self):
        """VLA elements are iterable."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<i", 3) + pystruct.pack("<iii", 1, 2, 3)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        values = [elem.value for elem in pkt.data]
        self.assertEqual(values, [1, 2, 3])

    def test_vla_indexing(self):
        """VLA elements are indexable."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<i", 3) + pystruct.pack("<iii", 100, 200, 300)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(pkt.data[0].value, 100)
        self.assertEqual(pkt.data[2].value, 300)

    def test_vla_write(self):
        """Write to VLA elements."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<i", 2) + pystruct.pack("<ii", 0, 0)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        pkt.data[0].value = 42
        pkt.data[1].value = 99
        self.assertEqual(pkt.data[0].value, 42)
        self.assertEqual(pkt.data[1].value, 99)

    def test_vla_must_be_last(self):
        """Field after VLA raises ValueError at size computation time."""
        class bad_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")
            extra: c_int

        with self.assertRaises(ValueError):
            size_of(bad_t)

    def test_vla_with_multiple_fixed(self):
        """Multiple fixed fields before VLA."""
        class msg_t(struct):
            type: c_int
            count: c_int
            data: array = vla_of(c_int, "count")

        raw = pystruct.pack("<ii", 1, 2) + pystruct.pack("<ii", 10, 20)
        memory = bytearray(raw)
        lib = inflater(memory)
        msg = lib.inflate(msg_t, 0)

        self.assertEqual(msg.type.value, 1)
        self.assertEqual(msg.count.value, 2)
        self.assertEqual(len(msg.data), 2)
        self.assertEqual(msg.data[0].value, 10)
        self.assertEqual(msg.data[1].value, 20)

    def test_vla_from_bytes(self):
        """from_bytes round-trip."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        raw = pystruct.pack("<iii", 2, 42, 99)
        pkt = packet_t.from_bytes(raw)

        self.assertEqual(pkt.length.value, 2)
        self.assertEqual(pkt.data[0].value, 42)
        self.assertEqual(pkt.data[1].value, 99)

    def test_vla_struct_elements(self):
        """VLA of structs."""
        class point_t(struct):
            x: c_int
            y: c_int

        class path_t(struct):
            count: c_int
            points: array = vla_of(point_t, "count")

        raw = pystruct.pack("<i", 2) + pystruct.pack("<iiii", 1, 2, 3, 4)
        memory = bytearray(raw)
        lib = inflater(memory)
        path = lib.inflate(path_t, 0)

        self.assertEqual(path.points[0].x.value, 1)
        self.assertEqual(path.points[0].y.value, 2)
        self.assertEqual(path.points[1].x.value, 3)
        self.assertEqual(path.points[1].y.value, 4)

    def test_vla_to_str(self):
        """to_str() shows VLA contents."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        raw = pystruct.pack("<ii", 1, 42)
        memory = bytearray(raw)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        s = pkt.to_str()
        self.assertIn("data:", s)
        self.assertIn("42", s)

    def test_vla_to_dict(self):
        """VLA appears as list in to_dict()."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        raw = pystruct.pack("<iii", 2, 10, 20)
        memory = bytearray(raw)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        d = pkt.to_dict()
        self.assertEqual(d["length"], 2)
        self.assertEqual(d["data"], [10, 20])


    def test_vla_dynamic_grow(self):
        """Changing the count field grows the VLA."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<iiiii", 2, 10, 20, 30, 40)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(len(pkt.data), 2)
        self.assertEqual(size_of(pkt), 4 + 2 * 4)

        pkt.length.value = 4
        self.assertEqual(len(pkt.data), 4)
        self.assertEqual(pkt.data[2].value, 30)
        self.assertEqual(pkt.data[3].value, 40)
        self.assertEqual(size_of(pkt), 4 + 4 * 4)

    def test_vla_dynamic_shrink(self):
        """Changing the count field shrinks the VLA."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<iiii", 3, 10, 20, 30)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        self.assertEqual(len(pkt.data), 3)

        pkt.length.value = 1
        self.assertEqual(len(pkt.data), 1)
        self.assertEqual(pkt.data[0].value, 10)
        self.assertEqual(size_of(pkt), 4 + 1 * 4)

    def test_vla_dynamic_to_bytes(self):
        """to_bytes reflects the current count after mutation."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<iiii", 3, 10, 20, 30)
        memory = bytearray(data)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)

        pkt.length.value = 2
        result = pkt.to_bytes()
        self.assertEqual(len(result), 4 + 2 * 4)

    def test_vla_negative_length(self):
        """Negative count raises ValueError."""
        class packet_t(struct):
            length: c_int
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<i", -3)
        memory = bytearray(data + b"\x00" * 32)
        lib = inflater(memory)

        with self.assertRaises(ValueError):
            lib.inflate(packet_t, 0)

    def test_vla_non_integer_count(self):
        """Non-integer count field raises TypeError."""
        from libdestruct import c_float

        class packet_t(struct):
            length: c_float
            data: array = vla_of(c_int, "length")

        data = pystruct.pack("<f", 3.5)
        memory = bytearray(data + b"\x00" * 32)
        lib = inflater(memory)

        with self.assertRaises(TypeError):
            lib.inflate(packet_t, 0)


class VLAInstanceSizeTest(unittest.TestCase):
    """`instance.size` on a VLA struct must report the dynamic size, not the class static size."""

    def test_vla_instance_size_matches_size_of(self):
        class packet_t(struct):
            length: c_int
            data: array[c_int, "length"]

        data = pystruct.pack("<i", 3) + pystruct.pack("<iii", 10, 20, 30)
        memory = bytearray(data)
        pkt = packet_t.from_bytes(memory)
        self.assertEqual(pkt.size, size_of(pkt))
        self.assertEqual(pkt.size, 16)

    def test_vla_instance_size_updates_when_count_changes(self):
        class packet_t(struct):
            length: c_int
            data: array[c_int, "length"]

        memory = bytearray(pystruct.pack("<i", 2) + pystruct.pack("<ii", 10, 20) + b"\x00" * 16)
        lib = inflater(memory)
        pkt = lib.inflate(packet_t, 0)
        self.assertEqual(pkt.size, 12)

        memory[0:4] = pystruct.pack("<i", 4)
        self.assertEqual(pkt.size, 20)


if __name__ == "__main__":
    unittest.main()
