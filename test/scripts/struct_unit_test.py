#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest
from enum import IntEnum

from libdestruct import c_int, c_long, c_uint, inflater, struct, ptr, ptr_to_self, array_of, enum, enum_of


class StructMemberCollisionTest(unittest.TestCase):
    """Struct fields named after obj properties should not crash."""

    def test_struct_with_value_field(self):
        class test_t(struct):
            value: c_int

        memory = (42).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.value.value, 42)

    def test_struct_with_address_field(self):
        class test_t(struct):
            address: c_int
            b: c_int

        memory = b""
        memory += (10).to_bytes(4, "little")
        memory += (20).to_bytes(4, "little")

        test = test_t.from_bytes(memory)
        self.assertEqual(test.address.value, 10)
        self.assertEqual(test.b.value, 20)

        # repr and get must not crash when 'address' is a member
        r = repr(test)
        self.assertIn("test_t", r)
        g = test.get()
        self.assertIn("test_t", g)

    def test_struct_with_size_field(self):
        class test_t(struct):
            size: c_int
            data: c_int

        memory = b""
        memory += (100).to_bytes(4, "little")
        memory += (200).to_bytes(4, "little")

        test = test_t.from_bytes(memory)
        self.assertEqual(test.size.value, 100)
        self.assertEqual(test.data.value, 200)

    def test_struct_with_resolver_field(self):
        class test_t(struct):
            resolver: c_int
            x: c_int

        memory = b""
        memory += (11).to_bytes(4, "little")
        memory += (22).to_bytes(4, "little")

        test = test_t.from_bytes(memory)
        self.assertEqual(test.resolver.value, 11)
        self.assertEqual(test.x.value, 22)

        # Internal address lookup must still work even though 'resolver' is a member
        addr = test.address
        self.assertIsInstance(addr, int)

        # repr/to_str must not crash
        r = repr(test)
        self.assertIn("test_t", r)
        s = test.to_str()
        self.assertIn("test_t", s)

    def test_struct_with_name_field(self):
        class test_t(struct):
            name: c_int

        memory = (77).to_bytes(4, "little")
        test = test_t.from_bytes(memory)
        self.assertEqual(test.name.value, 77)

        # to_str/repr must use the struct type name, not the member value
        s = test.to_str()
        self.assertTrue(s.startswith("test_t"))
        r = repr(test)
        self.assertIn("test_t", r)

    def test_nested_struct_with_collisions(self):
        class inner_t(struct):
            value: c_int

        class outer_t(struct):
            address: inner_t
            size: c_int

        memory = b""
        memory += (10).to_bytes(4, "little")
        memory += (20).to_bytes(4, "little")

        test = outer_t.from_bytes(memory)
        self.assertEqual(test.address.value.value, 10)
        self.assertEqual(test.size.value, 20)


class StructRoundTripTest(unittest.TestCase):
    """Struct serialization round-trips."""

    def test_simple_round_trip(self):
        class test_t(struct):
            a: c_int
            b: c_long

        memory = b""
        memory += (42).to_bytes(4, "little")
        memory += (1337).to_bytes(8, "little")

        test = test_t.from_bytes(memory)
        self.assertEqual(test.to_bytes(), memory[:12])

    def test_nested_struct_round_trip(self):
        class inner_t(struct):
            x: c_int
            y: c_int

        class outer_t(struct):
            a: c_int
            b: inner_t

        memory = b""
        memory += (1).to_bytes(4, "little")
        memory += (2).to_bytes(4, "little")
        memory += (3).to_bytes(4, "little")

        test = outer_t.from_bytes(memory)
        self.assertEqual(test.to_bytes(), memory[:12])

    def test_struct_to_str(self):
        class test_t(struct):
            a: c_int
            b: c_int

        memory = b""
        memory += (10).to_bytes(4, "little")
        memory += (20).to_bytes(4, "little")

        test = test_t.from_bytes(memory)
        s = test.to_str()
        self.assertIn("a: 10", s)
        self.assertIn("b: 20", s)

    def test_struct_repr(self):
        class test_t(struct):
            a: c_int

        memory = (99).to_bytes(4, "little")
        test = test_t.from_bytes(memory)

        r = repr(test)
        self.assertIn("test_t", r)

    def test_bytes_on_bytearray_backed_struct(self):
        class test_t(struct):
            a: c_int
            b: c_int

        lib = inflater(bytearray(b"\x01\x00\x00\x00\x02\x00\x00\x00"))
        test = lib.inflate(test_t, 0)

        result = bytes(test)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 8)


class StructFreezeTest(unittest.TestCase):
    """Struct freeze semantics."""

    def test_frozen_struct_rejects_writes(self):
        class test_t(struct):
            a: c_int
            b: c_int

        memory = bytearray(b"\x00" * 8)
        lib = inflater(memory)
        test = lib.inflate(test_t, 0)
        test.a.value = 10
        test.b.value = 20

        test.freeze()

        self.assertEqual(test.a.value, 10)
        self.assertEqual(test.b.value, 20)

        with self.assertRaises(ValueError):
            test.a.value = 999


class ForwardRefPtrTest(unittest.TestCase):
    """Forward reference ptr["Type"] syntax."""

    def test_self_referential_struct(self):
        class Node(struct):
            val: c_int
            next: ptr["Node"]

        # No padding: c_int(4) + ptr(8) = 12 bytes per node
        memory = b""
        memory += (10).to_bytes(4, "little")
        memory += (12).to_bytes(8, "little")  # next -> offset 12
        memory += (20).to_bytes(4, "little")
        memory += (0).to_bytes(8, "little")   # next -> null

        node = Node.from_bytes(memory)
        self.assertEqual(node.val.value, 10)
        self.assertEqual(node.next.unwrap().val.value, 20)

    def test_tree_struct(self):
        class TreeNode(struct):
            data: c_uint
            left: ptr["TreeNode"]
            right: ptr["TreeNode"]

        # Single node, no children
        # c_uint(4) + ptr(8) + ptr(8) = 20 bytes
        memory = b""
        memory += (42).to_bytes(4, "little")
        memory += (0).to_bytes(4, "little")   # padding
        memory += (0).to_bytes(8, "little")   # left=null
        memory += (0).to_bytes(8, "little")   # right=null

        node = TreeNode.from_bytes(memory)
        self.assertEqual(node.data.value, 42)


class StructEqualityTest(unittest.TestCase):
    def test_struct_eq_non_struct_returns_not_implemented(self):
        """struct.__eq__ returns NotImplemented for non-struct values."""
        class s_t(struct):
            x: c_int

        s = s_t.from_bytes(b"\x01\x00\x00\x00")
        self.assertIs(s.__eq__(42), NotImplemented)


if __name__ == "__main__":
    unittest.main()
