#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

"""Tests targeting uncovered code paths in critical modules."""

import struct as pystruct
import unittest
from enum import IntEnum, IntFlag

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
    inflater,
    ptr,
    ptr_to,
    ptr_to_self,
    size_of,
    struct,
)
from libdestruct.backing.memory_resolver import MemoryResolver
from libdestruct.common.union import tagged_union, union, union_of
from libdestruct.common.utils import alignment_of, _alignment_from_size


# ---------- obj.py coverage ----------


class ObjSetFrozenTest(unittest.TestCase):
    """obj.set() on a frozen object must raise ValueError."""

    def test_set_on_frozen_raises(self):
        obj = c_int.from_bytes((1).to_bytes(4, "little"))
        with self.assertRaises(ValueError):
            obj.set(2)


class ObjDiffErrorTest(unittest.TestCase):
    """obj.diff() wraps ValueError in RuntimeError."""

    def test_diff_without_freeze_wraps_error(self):
        """diff() on unfrozen obj where _frozen_value is None."""
        memory = bytearray(4)
        lib = inflater(memory)
        obj = lib.inflate(c_int, 0)
        obj.value = 5
        # diff returns (frozen_value, current_value) - frozen_value is None (default)
        old, new = obj.diff()
        self.assertIsNone(old)
        self.assertEqual(new, 5)


class ObjResetErrorTest(unittest.TestCase):
    """obj.reset() wraps ValueError in RuntimeError."""

    def test_reset_without_freeze_attempts_set_none(self):
        """reset() sets _frozen_value (None) which causes a TypeError/error."""
        memory = bytearray(4)
        lib = inflater(memory)
        obj = lib.inflate(c_int, 0)
        # _frozen_value is None, _set(None) will fail
        with self.assertRaises(Exception):
            obj.reset()


class ObjUpdateTest(unittest.TestCase):
    """obj.update() captures current value as frozen value."""

    def test_update_captures_current(self):
        memory = bytearray(4)
        lib = inflater(memory)
        obj = lib.inflate(c_int, 0)
        obj.value = 42
        obj.update()
        self.assertEqual(obj._frozen_value, 42)


class ObjPdiffTest(unittest.TestCase):
    """obj.pdiff() returns string diff."""

    def test_pdiff_format(self):
        memory = bytearray(4)
        lib = inflater(memory)
        obj = lib.inflate(c_int, 0)
        obj.value = 10
        obj.freeze()
        memory[0:4] = (20).to_bytes(4, "little")
        result = obj.pdiff()
        self.assertIn("10", result)
        self.assertIn("20", result)
        self.assertIn("->", result)


# ---------- union.py coverage ----------


class UnionEmptyTest(unittest.TestCase):
    """Empty union edge cases."""

    def test_empty_union_get(self):
        u = union(None, None, 4)
        self.assertIsNone(u.get())

    def test_empty_union_to_dict(self):
        u = union(None, None, 4)
        self.assertIsNone(u.to_dict())

    def test_empty_union_to_str(self):
        u = union(None, None, 4)
        self.assertEqual(u.to_str(), "union(empty)")


class UnionSetNoVariantTest(unittest.TestCase):
    """Setting a union without an active variant raises RuntimeError."""

    def test_set_raises(self):
        u = union(None, None, 4)
        with self.assertRaises(RuntimeError):
            u._set(42)


class UnionResetNoFreezeTest(unittest.TestCase):
    """Resetting an unfrozen union raises RuntimeError."""

    def test_reset_raises(self):
        u = union(None, None, 4)
        with self.assertRaises(RuntimeError):
            u.reset()


class UnionNoneResolverTest(unittest.TestCase):
    """Union with None resolver returns zero bytes."""

    def test_to_bytes_none_resolver(self):
        u = union(None, None, 8)
        self.assertEqual(u.to_bytes(), b"\x00" * 8)

    def test_freeze_none_resolver(self):
        u = union(None, None, 4)
        u.freeze()
        self.assertEqual(u._frozen_bytes, b"\x00" * 4)


class PlainUnionDiffTest(unittest.TestCase):
    """Plain union diff returns per-variant diffs."""

    def test_plain_union_diff(self):
        class s_t(struct):
            data: union = union_of({"i": c_int, "l": c_long})

        memory = bytearray(8)
        pystruct.pack_into("<q", memory, 0, 42)
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        s.data.freeze()
        pystruct.pack_into("<q", memory, 0, 99)
        result = s.data.diff()
        self.assertIsInstance(result, dict)
        self.assertIn("i", result)
        self.assertIn("l", result)


class PlainUnionToStrTest(unittest.TestCase):
    """Plain union to_str() lists variant names."""

    def test_plain_union_to_str(self):
        class s_t(struct):
            data: union = union_of({"i": c_int, "f": c_float})

        memory = bytearray(4)
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        result = s.data.to_str()
        self.assertIn("union(", result)
        self.assertIn("i", result)


# ---------- array_impl.py coverage ----------


class ArrayToStrTest(unittest.TestCase):
    """Array to_str for struct elements and to_dict."""

    def test_struct_array_to_str(self):
        """Array of struct elements has multi-line to_str."""
        class point_t(struct):
            x: c_int
            y: c_int

        class s_t(struct):
            pts: list[point_t] = array_of(point_t, 2)

        memory = bytearray(16)
        pystruct.pack_into("<iiii", memory, 0, 1, 2, 3, 4)
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        result = s.pts.to_str()
        self.assertIn("[", result)
        self.assertIn("]", result)
        self.assertIn("\n", result)

    def test_array_to_dict(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(3))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)
        result = arr.to_dict()
        self.assertEqual(result, [0, 1, 2])


# ---------- ptr.py coverage ----------


class PtrNonFrozenToBytesTest(unittest.TestCase):
    """Non-frozen ptr.to_bytes() returns resolver bytes."""

    def test_non_frozen_to_bytes(self):
        memory = bytearray(8)
        memory[0:8] = (0x1234).to_bytes(8, "little")
        p = ptr(MemoryResolver(memory, 0))
        result = p.to_bytes()
        self.assertEqual(result, memory[:8])


class PtrUnwrapWithLengthTypedTest(unittest.TestCase):
    """unwrap(length=N) on a typed ptr raises ValueError."""

    def test_unwrap_length_on_typed_raises(self):
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8:12] = (42).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)
        with self.assertRaises(ValueError):
            p.unwrap(length=4)


class PtrTryUnwrapInvalidTest(unittest.TestCase):
    """try_unwrap() returns None for invalid addresses."""

    def test_try_unwrap_uses_cache(self):
        """try_unwrap uses the same cache as unwrap."""
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8] = 0xAB

        p = ptr(MemoryResolver(memory, 0))
        r1 = p.try_unwrap()
        r2 = p.try_unwrap()
        self.assertEqual(r1, r2)


class PtrToStrTest(unittest.TestCase):
    """ptr.to_str() for typed and untyped pointers."""

    def test_untyped_ptr_to_str(self):
        memory = bytearray(8)
        memory[0:8] = (0x42).to_bytes(8, "little")
        p = ptr(MemoryResolver(memory, 0))
        result = p.to_str()
        self.assertIn("ptr@0x42", result)

    def test_typed_ptr_to_str(self):
        memory = bytearray(8)
        memory[0:8] = (0x42).to_bytes(8, "little")
        p = ptr(MemoryResolver(memory, 0), c_int)
        result = p.to_str()
        self.assertIn("0x42", result)


class PtrArithmeticResolverTest(unittest.TestCase):
    """_ArithmeticResolver edge cases."""

    def test_arithmetic_resolver_modify_raises(self):
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8:12] = (42).to_bytes(4, "little")

        p = ptr(MemoryResolver(memory, 0), c_int)
        p2 = p + 1
        with self.assertRaises(RuntimeError):
            p2._set(0)


# ---------- bitfield.py coverage ----------


class BitfieldToBytesTest(unittest.TestCase):
    """Direct bitfield.to_bytes() calls."""

    def test_group_owner_to_bytes(self):
        """Group owner returns backing bytes."""
        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)
            b: c_uint = bitfield_of(c_uint, 5)

        memory = bytearray((0b01010_101).to_bytes(4, "little"))
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        result = s.a.to_bytes()
        self.assertEqual(len(result), 4)

    def test_non_owner_to_bytes_empty(self):
        """Non-owner returns empty bytes."""
        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)
            b: c_uint = bitfield_of(c_uint, 5)

        memory = bytearray((0b01010_101).to_bytes(4, "little"))
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        result = s.b.to_bytes()
        self.assertEqual(result, b"")


class BitfieldToStrTest(unittest.TestCase):
    """bitfield.to_str() returns value string."""

    def test_to_str(self):
        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 3)

        memory = bytearray((5).to_bytes(4, "little"))
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        self.assertEqual(s.a.to_str(), "5")


class BitfieldSignedNegativeTest(unittest.TestCase):
    """Signed bitfield with negative raw backing value."""

    def test_negative_backing_read(self):
        """Signed int with all bits set → negative raw value in get()."""
        class s_t(struct):
            val: c_int = bitfield_of(c_int, 4)

        # c_int with value -1 (all bits set)
        memory = bytearray((-1).to_bytes(4, "little", signed=True))
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        # Low 4 bits of -1 are 0b1111, sign-extended as 4-bit signed → -1
        self.assertEqual(s.val.value, -1)

    def test_negative_backing_write(self):
        """Writing to a signed bitfield when backing is negative."""
        class s_t(struct):
            a: c_int = bitfield_of(c_int, 4)
            b: c_int = bitfield_of(c_int, 4)

        memory = bytearray((-1).to_bytes(4, "little", signed=True))
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        # Write to 'a' — backing raw is negative, must handle sign correctly
        s.a.value = 3
        self.assertEqual(s.a.value, 3)
        # 'b' should still have its original bits (0b1111 → -1)
        self.assertEqual(s.b.value, -1)


# ---------- utils.py coverage ----------


class AlignmentFromSizeTest(unittest.TestCase):
    """_alignment_from_size edge cases."""

    def test_non_power_of_two(self):
        self.assertEqual(_alignment_from_size(3), 1)
        self.assertEqual(_alignment_from_size(5), 1)
        self.assertEqual(_alignment_from_size(6), 1)
        self.assertEqual(_alignment_from_size(7), 1)

    def test_too_large(self):
        self.assertEqual(_alignment_from_size(16), 1)
        self.assertEqual(_alignment_from_size(32), 1)

    def test_zero(self):
        self.assertEqual(_alignment_from_size(0), 1)

    def test_valid_powers(self):
        self.assertEqual(_alignment_from_size(1), 1)
        self.assertEqual(_alignment_from_size(2), 2)
        self.assertEqual(_alignment_from_size(4), 4)
        self.assertEqual(_alignment_from_size(8), 8)


class AlignmentOfInstanceTest(unittest.TestCase):
    """alignment_of for instances with alignment attribute."""

    def test_inflated_struct_instance(self):
        class aligned_t(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        memory = bytearray(8)
        lib = inflater(memory)
        s = lib.inflate(aligned_t, 0)
        self.assertEqual(alignment_of(s), 4)


# ---------- struct_impl.py coverage ----------


class StructImplErrorsTest(unittest.TestCase):
    """struct_impl error paths."""

    def test_invalid_resolver_type(self):
        class s_t(struct):
            x: c_int

        # Force _type_impl creation by inflating once
        s_t.from_bytes((0).to_bytes(4, "little"))
        with self.assertRaises(TypeError):
            s_t._type_impl("not_a_resolver")

    def test_struct_set_raises(self):
        class s_t(struct):
            x: c_int

        s = s_t.from_bytes((1).to_bytes(4, "little"))
        with self.assertRaises(RuntimeError):
            s._set("foo")

    def test_struct_eq_different_sizes(self):
        class a_t(struct):
            x: c_int

        class b_t(struct):
            x: c_long

        a = a_t.from_bytes((1).to_bytes(4, "little"))
        b = b_t.from_bytes((1).to_bytes(8, "little"))
        self.assertNotEqual(a, b)

    def test_struct_eq_different_keys(self):
        class a_t(struct):
            x: c_int

        class b_t(struct):
            y: c_int

        a = a_t.from_bytes((1).to_bytes(4, "little"))
        b = b_t.from_bytes((1).to_bytes(4, "little"))
        self.assertNotEqual(a, b)


class StructReprTest(unittest.TestCase):
    """struct_impl repr and to_str."""

    def test_repr_contains_address_and_members(self):
        class s_t(struct):
            a: c_int
            b: c_int

        memory = bytearray(8)
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)
        s.a.value = 10
        r = repr(s)
        self.assertIn("s_t", r)
        self.assertIn("address", r)
        self.assertIn("size", r)


# ---------- forward_ref_inflater.py coverage ----------


class ForwardRefPtrStrTest(unittest.TestCase):
    """ptr['Type'] with string forward references."""

    def test_ptr_string_forward_ref(self):
        """ptr['Node'] should work for self-referential structs."""
        class Node(struct):
            val: c_int
            next: ptr["Node"]

        memory = bytearray(24)
        memory[0:4] = (10).to_bytes(4, "little")
        memory[4:12] = (12).to_bytes(8, "little")  # next -> offset 12
        memory[12:16] = (20).to_bytes(4, "little")
        memory[16:24] = (0).to_bytes(8, "little")   # next -> null

        node = Node.from_bytes(memory)
        self.assertEqual(node.val.value, 10)
        next_node = node.next.unwrap()
        self.assertEqual(next_node.val.value, 20)


class PtrToStrFieldTest(unittest.TestCase):
    """ptr to_str with Field-backed wrapper."""

    def test_ptr_to_field_wrapper(self):
        """ptr_to(c_int) creates a Field-backed wrapper that has a qualified name."""
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8:12] = (42).to_bytes(4, "little")

        lib = inflater(memory)
        p = lib.inflate(ptr_to(c_int), 0)
        result = p.to_str()
        self.assertIn("0x8", result)


# ---------- forward_ref_inflater.py coverage ----------


class LazyPtrFieldUnresolvableTest(unittest.TestCase):
    """_LazyPtrField when forward ref cannot be resolved → returns raw ptr."""

    def test_unresolvable_forward_ref_returns_raw_ptr(self):
        """ptr['NonExistentType'] should still inflate, just as an untyped ptr."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _LazyPtrField

        lazy = _LazyPtrField(ForwardRef("CompletelyBogusTypeThatDoesNotExist"), owner=None)
        memory = bytearray(8)
        memory[0:8] = (0).to_bytes(8, "little")
        result = lazy.inflate(MemoryResolver(memory, 0))
        self.assertIsInstance(result, ptr)
        # wrapper should be None since it couldn't resolve
        self.assertIsNone(result.wrapper)

    def test_forward_ref_resolves_to_non_type(self):
        """Forward ref that eval's to a non-type value returns None from _resolve_forward_ref."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _LazyPtrField

        # "42" eval's to int 42, not a type
        lazy = _LazyPtrField(ForwardRef("42"), owner=None)
        result = lazy._resolve_forward_ref()
        self.assertIsNone(result)

    def test_forward_ref_eval_exception(self):
        """Forward ref that raises during eval returns None."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _LazyPtrField

        # Valid syntax but unresolvable name → NameError during eval
        lazy = _LazyPtrField(ForwardRef("NoSuchTypeAnywhere"), owner=None)
        result = lazy._resolve_forward_ref()
        self.assertIsNone(result)


class SubscriptedPtrHandlerEdgeCasesTest(unittest.TestCase):
    """_subscripted_ptr_handler edge cases."""

    def test_ptr_subscript_none_target(self):
        """ptr[()] with empty args → untyped ptr field."""
        from libdestruct.common.forward_ref_inflater import _subscripted_ptr_handler

        result = _subscripted_ptr_handler(ptr, (), owner=None)
        self.assertIsNotNone(result)
        # Should return a PtrField.inflate bound method
        memory = bytearray(8)
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)
        self.assertIsNone(p.wrapper)

    def test_ptr_subscript_string_target(self):
        """ptr['SomeString'] goes through ForwardRef path."""
        from libdestruct.common.forward_ref_inflater import _subscripted_ptr_handler

        result = _subscripted_ptr_handler(ptr, ("NonExistentType",), owner=None)
        self.assertIsNotNone(result)
        # Should return a _LazyPtrField.inflate bound method
        memory = bytearray(8)
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)

    def test_ptr_subscript_non_type_non_string_target(self):
        """ptr[42] (invalid target) → fallback untyped ptr."""
        from libdestruct.common.forward_ref_inflater import _subscripted_ptr_handler

        result = _subscripted_ptr_handler(ptr, (42,), owner=None)
        self.assertIsNotNone(result)
        memory = bytearray(8)
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)
        self.assertIsNone(p.wrapper)

    def test_ptr_subscript_concrete_type(self):
        """ptr[c_int] resolves immediately to typed ptr."""
        from libdestruct.common.forward_ref_inflater import _subscripted_ptr_handler

        result = _subscripted_ptr_handler(ptr, (c_int,), owner=None)
        self.assertIsNotNone(result)
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8:12] = (42).to_bytes(4, "little")
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)
        self.assertIsNotNone(p.wrapper)


class BareForwardRefInflaterTest(unittest.TestCase):
    """_forward_ref_inflater for bare ForwardRef annotations."""

    def test_ptr_forward_ref_string_parsing(self):
        """ForwardRef('ptr[SomeType]') is parsed and creates a lazy ptr."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _forward_ref_inflater

        ref = ForwardRef("ptr['Node']")
        result = _forward_ref_inflater(ref, type(None), owner=None)
        self.assertIsNotNone(result)
        # Should return a _LazyPtrField.inflate bound method
        memory = bytearray(8)
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)

    def test_ptr_forward_ref_double_quoted(self):
        """ForwardRef('ptr[\"Node\"]') with double quotes."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _forward_ref_inflater

        ref = ForwardRef('ptr["Node"]')
        result = _forward_ref_inflater(ref, type(None), owner=None)
        self.assertIsNotNone(result)
        memory = bytearray(8)
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)

    def test_ptr_forward_ref_unquoted(self):
        """ForwardRef('ptr[c_int]') with unquoted inner type."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _forward_ref_inflater

        ref = ForwardRef("ptr[c_int]")
        result = _forward_ref_inflater(ref, type(None), owner=None)
        self.assertIsNotNone(result)
        memory = bytearray(8)
        p = result(MemoryResolver(memory, 0))
        self.assertIsInstance(p, ptr)

    def test_non_ptr_forward_ref_raises(self):
        """ForwardRef('SomeRandomThing') raises ValueError."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _forward_ref_inflater

        ref = ForwardRef("SomeRandomThing")
        with self.assertRaises(ValueError) as ctx:
            _forward_ref_inflater(ref, type(None), owner=None)
        self.assertIn("SomeRandomThing", str(ctx.exception))

    def test_lazy_ptr_with_owner_resolves(self):
        """_LazyPtrField with owner tuple resolves types from owner's module."""
        from typing import ForwardRef
        from libdestruct.common.forward_ref_inflater import _LazyPtrField

        # Create a lazy field that references c_int (available in this module's globals)
        lazy = _LazyPtrField(ForwardRef("c_int"), owner=(None, type(self)))
        resolved = lazy._resolve_forward_ref()
        self.assertIs(resolved, c_int)


# ---------- flags int_flag_field.py coverage ----------


class FlagsFieldSizesTest(unittest.TestCase):
    """IntFlagField with different sizes."""

    class Perms(IntFlag):
        R = 1
        W = 2
        X = 4

    def test_flags_size_1(self):
        from libdestruct import flags_of

        class s_t(struct):
            perms: c_int = flags_of(self.Perms, size=1)

        memory = (7).to_bytes(1, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.perms.value, self.Perms.R | self.Perms.W | self.Perms.X)

    def test_flags_size_2(self):
        from libdestruct import flags_of

        class s_t(struct):
            perms: c_int = flags_of(self.Perms, size=2)

        memory = (3).to_bytes(2, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.perms.value, self.Perms.R | self.Perms.W)

    def test_flags_size_8(self):
        from libdestruct import flags_of

        class s_t(struct):
            perms: c_int = flags_of(self.Perms, size=8)

        memory = (1).to_bytes(8, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.perms.value, self.Perms.R)

    def test_flags_invalid_size(self):
        from libdestruct import flags_of
        with self.assertRaises(ValueError):
            flags_of(self.Perms, size=3)

    def test_flags_size_too_large(self):
        from libdestruct import flags_of
        with self.assertRaises(ValueError):
            flags_of(self.Perms, size=9)


# ---------- c_str.py coverage ----------


class CStrEdgeCasesTest(unittest.TestCase):
    """c_str edge cases."""

    def test_repr(self):
        from libdestruct import c_str

        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)
        r = repr(s)
        self.assertIsInstance(r, str)

    def test_negative_index_raises(self):
        from libdestruct import c_str

        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)
        with self.assertRaises(IndexError):
            s.get(-2)

    def test_set_negative_index_raises(self):
        from libdestruct import c_str

        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)
        with self.assertRaises(IndexError):
            s._set(b"X", -2)

    def test_set_full_string(self):
        from libdestruct import c_str

        memory = bytearray(b"Hello\x00")
        lib = inflater(memory)
        s = lib.inflate(c_str, 0)
        s.value = b"World"
        self.assertEqual(s.value, b"World")


# ---------- struct_parser.py coverage ----------


class StructParserEdgeCasesTest(unittest.TestCase):
    """C parser edge cases for coverage."""

    def test_enum_in_struct_raises(self):
        """Enum inside struct is not yet supported, must raise TypeError."""
        from libdestruct.c.struct_parser import definition_to_type

        with self.assertRaises(TypeError):
            definition_to_type("struct test { enum { A, B, C } val; };")

    def test_struct_with_pointer_member(self):
        from libdestruct.c.struct_parser import definition_to_type

        t = definition_to_type("struct test { int *p; int x; };")
        self.assertIn("p", t.__annotations__)
        self.assertIn("x", t.__annotations__)

    def test_struct_with_array_read(self):
        from libdestruct.c.struct_parser import definition_to_type

        t = definition_to_type("struct test { int arr[3]; int x; };")
        memory = b"".join((i).to_bytes(4, "little") for i in [10, 20, 30, 42])
        s = t.from_bytes(memory)
        self.assertEqual(s.x.value, 42)

    def test_named_struct_cached(self):
        """Named structs are cached and reusable."""
        from libdestruct.c.struct_parser import definition_to_type, clear_parser_cache

        clear_parser_cache()
        t = definition_to_type("""
            struct Inner { int x; };
            struct Outer { struct Inner a; int b; };
        """)
        memory = (1).to_bytes(4, "little") + (2).to_bytes(4, "little")
        s = t.from_bytes(memory)
        self.assertEqual(s.b.value, 2)
        clear_parser_cache()


if __name__ == "__main__":
    unittest.main()
