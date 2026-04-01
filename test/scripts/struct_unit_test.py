#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest
from enum import IntEnum

from typing import Annotated

from libdestruct import array, c_int, c_long, c_short, c_uint, c_ushort, inflater, offset, struct, ptr, ptr_to_self, array_of, enum, enum_of, size_of, bitfield_of
from libdestruct.common.union import union, union_of, tagged_union


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

    def test_frozen_struct_value_not_none(self):
        """Frozen struct .value should not be None."""
        class test_t(struct):
            a: c_int

        memory = bytearray(b"\x2a\x00\x00\x00")
        lib = inflater(memory)
        test = lib.inflate(test_t, 0)
        test.freeze()
        self.assertIsNotNone(test.value)

    def test_from_bytes_struct_is_frozen(self):
        """struct.from_bytes should return a frozen struct, like obj.from_bytes."""
        class test_t(struct):
            a: c_int

        test = test_t.from_bytes(b"\x2a\x00\x00\x00")
        self.assertTrue(test._frozen)

    def test_from_bytes_struct_rejects_writes(self):
        """struct.from_bytes result should reject writes with ValueError, not TypeError."""
        class test_t(struct):
            a: c_int

        test = test_t.from_bytes(b"\x2a\x00\x00\x00")
        with self.assertRaises(ValueError):
            test.a.value = 99


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


class SubscriptSyntaxTest(unittest.TestCase):
    """Test the subscript syntax: enum[T], array[T, N], ptr[T]."""

    def test_enum_subscript(self):
        """enum[MyEnum] works as a type annotation for struct fields."""
        class Color(IntEnum):
            RED = 0
            GREEN = 1
            BLUE = 2

        class s_t(struct):
            color: enum[Color]

        memory = (1).to_bytes(4, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.color.value, Color.GREEN)

    def test_enum_subscript_custom_backing(self):
        """enum[MyEnum, c_short] uses a custom backing type."""
        class Status(IntEnum):
            OFF = 0
            ON = 1

        class s_t(struct):
            status: enum[Status, c_short]

        memory = (1).to_bytes(2, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.status.value, Status.ON)
        from libdestruct import size_of
        self.assertEqual(size_of(s_t), 2)

    def test_array_subscript(self):
        """array[c_int, 3] works as a type annotation for struct fields."""
        class s_t(struct):
            data: array[c_int, 3]

        memory = b""
        for v in [10, 20, 30]:
            memory += v.to_bytes(4, "little")

        s = s_t.from_bytes(memory)
        self.assertEqual(s.data[0].value, 10)
        self.assertEqual(s.data[1].value, 20)
        self.assertEqual(s.data[2].value, 30)

    def test_array_subscript_size(self):
        """array[c_int, 3] has correct size."""
        class s_t(struct):
            data: array[c_int, 3]

        from libdestruct import size_of
        self.assertEqual(size_of(s_t), 12)

    def test_ptr_subscript(self):
        """ptr[T] works as a type annotation (already supported)."""
        class s_t(struct):
            val: c_int
            ref: ptr[c_int]

        memory = b""
        memory += (42).to_bytes(4, "little")
        memory += (0).to_bytes(8, "little")

        s = s_t.from_bytes(memory)
        self.assertEqual(s.val.value, 42)

    def test_mixed_subscript_struct(self):
        """Struct mixing all subscript syntaxes."""
        class Direction(IntEnum):
            UP = 0
            DOWN = 1

        class s_t(struct):
            dir: enum[Direction]
            coords: array[c_int, 2]
            next: ptr["s_t"]

        memory = b""
        memory += (1).to_bytes(4, "little")          # dir = DOWN
        memory += (10).to_bytes(4, "little")          # coords[0]
        memory += (20).to_bytes(4, "little")          # coords[1]
        memory += (0).to_bytes(8, "little")           # next = null

        s = s_t.from_bytes(memory)
        self.assertEqual(s.dir.value, Direction.DOWN)
        self.assertEqual(s.coords[0].value, 10)
        self.assertEqual(s.coords[1].value, 20)


class AnnotatedOffsetTest(unittest.TestCase):
    """Test Annotated[type, offset(N)] syntax for explicit field offsets."""

    def test_annotated_offset_basic(self):
        """Annotated[c_int, offset(N)] places a field at the given offset."""
        class s_t(struct):
            a: c_int
            b: Annotated[c_int, offset(8)]

        from libdestruct import size_of
        self.assertEqual(size_of(s_t), 12)  # 8 + 4

    def test_annotated_offset_read(self):
        """Values are read correctly from Annotated offset positions."""
        import struct as pystruct

        class s_t(struct):
            a: c_int
            b: Annotated[c_int, offset(8)]

        memory = pystruct.pack("<i", 10) + b"\x00" * 4 + pystruct.pack("<i", 20)
        s = s_t.from_bytes(memory)
        self.assertEqual(s.a.value, 10)
        self.assertEqual(s.b.value, 20)

    def test_annotated_offset_with_subscript(self):
        """Annotated works with subscript syntax types."""
        class s_t(struct):
            a: c_int
            data: Annotated[array[c_int, 2], offset(8)]

        from libdestruct import size_of
        self.assertEqual(size_of(s_t), 16)  # 8 + 2*4

    def test_annotated_offset_with_ptr(self):
        """Annotated works with ptr subscript syntax."""
        class s_t(struct):
            a: c_int
            ref: Annotated[ptr[c_int], offset(8)]

        from libdestruct import size_of
        self.assertEqual(size_of(s_t), 16)  # 8 + 8

    def test_old_offset_syntax_still_works(self):
        """The old offset() default value syntax continues to work."""
        class s_t(struct):
            a: c_int
            b: c_int = offset(8)

        from libdestruct import size_of
        self.assertEqual(size_of(s_t), 12)


class StructEqualityTest(unittest.TestCase):
    def test_struct_eq_non_struct_returns_not_implemented(self):
        """struct.__eq__ returns NotImplemented for non-struct values."""
        class s_t(struct):
            x: c_int

        s = s_t.from_bytes(b"\x01\x00\x00\x00")
        self.assertIs(s.__eq__(42), NotImplemented)


class BitfieldExplicitOffsetTest(unittest.TestCase):
    """Explicit offset after bitfields must flush the pending bitfield group first."""

    def test_offset_after_bitfield_size(self):
        """Struct size must be correct when offset() follows bitfield fields."""
        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 1)
            b: c_int = offset(8)

        # a is a 1-bit bitfield in a 4-byte c_uint group at offset 0.
        # b is at explicit offset 8 with size 4.
        # Total size: 8 + 4 = 12
        self.assertEqual(size_of(s_t), 12)

    def test_offset_after_bitfield_read(self):
        """Values must be read correctly when offset() follows bitfield fields."""
        import struct as pystruct

        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 1)
            b: c_int = offset(8)

        memory = bytearray(12)
        memory[0:4] = pystruct.pack("<I", 1)   # a = 1
        memory[8:12] = pystruct.pack("<i", 42)  # b = 42

        s = s_t.from_bytes(memory)
        self.assertEqual(s.a.value, 1)
        self.assertEqual(s.b.value, 42)


class UnionAlignmentTest(unittest.TestCase):
    """Union fields in aligned structs must use member-derived alignment."""

    def test_plain_union_alignment_non_power_of_two_size(self):
        """Union of a 12-byte packed struct and c_long: size=12 but alignment must be 8 (from c_long)."""
        class triple_t(struct):
            a: c_int
            b: c_int
            c: c_int

        # triple_t is a packed 12-byte struct with alignment 1
        # c_long is 8 bytes with alignment 8
        # union size = 12, but alignment should be 8 (max member alignment)
        class s_t(struct):
            _aligned_ = True
            tag: c_short  # 2 bytes, align 2
            data: union = union_of({"t": triple_t, "l": c_long})

        # tag at offset 0 (2 bytes)
        # data alignment = 8 → data at offset 8
        # data size = 12
        # struct max alignment = 8 → total = _align_offset(20, 8) = 24
        self.assertEqual(size_of(s_t), 24)

    def test_tagged_union_alignment_non_power_of_two_size(self):
        """Tagged union of a 12-byte packed struct and c_long: alignment must be 8."""
        class triple_t(struct):
            a: c_int
            b: c_int
            c: c_int

        class s_t(struct):
            _aligned_ = True
            tag: c_int  # 4 bytes, align 4
            data: union = tagged_union("tag", {0: triple_t, 1: c_long})

        # tag at offset 0 (4 bytes)
        # data alignment = 8 → data at offset 8
        # data size = 12
        # struct max alignment = 8 → total = _align_offset(20, 8) = 24
        self.assertEqual(size_of(s_t), 24)


class SubscriptedEnumUnsignedTest(unittest.TestCase):
    """enum[E, unsigned_backing] must preserve signedness."""

    def test_enum_unsigned_backing(self):
        """enum[E, c_ushort] should correctly decode values exceeding signed range."""
        from enum import IntEnum

        class E(IntEnum):
            MAX_VAL = 0xFFFF

        class s_t(struct):
            val: enum[E, c_ushort]

        memory = (0xFFFF).to_bytes(2, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.val.value, E.MAX_VAL)

    def test_enum_unsigned_size(self):
        """enum[E, c_ushort] struct should be 2 bytes."""
        from enum import IntEnum

        class E(IntEnum):
            A = 0

        class s_t(struct):
            val: enum[E, c_ushort]

        self.assertEqual(size_of(s_t), 2)


if __name__ == "__main__":
    unittest.main()
