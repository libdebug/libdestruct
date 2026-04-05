#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

"""Tests that expose bugs found during the second-pass code review."""

import unittest

from libdestruct import (
    array,
    bitfield_of,
    c_int,
    c_uint,
    inflater,
    size_of,
    struct,
)
from libdestruct.c.struct_parser import clear_parser_cache, definition_to_type


class ComparisonOperatorSafetyTest(unittest.TestCase):
    """Comparison operators must not raise TypeError for incompatible obj types."""

    def test_lt_primitive_vs_struct_returns_not_implemented(self):
        """c_int < struct should return NotImplemented, not raise TypeError."""
        class s_t(struct):
            x: c_int

        memory = bytearray(4)
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        s = lib.inflate(s_t, 0)

        # Must not raise TypeError
        result = val.__lt__(s)
        self.assertIs(result, NotImplemented)

    def test_gt_primitive_vs_struct_returns_not_implemented(self):
        class s_t(struct):
            x: c_int

        memory = bytearray(4)
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        s = lib.inflate(s_t, 0)

        result = val.__gt__(s)
        self.assertIs(result, NotImplemented)

    def test_le_primitive_vs_struct_returns_not_implemented(self):
        class s_t(struct):
            x: c_int

        memory = bytearray(4)
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        s = lib.inflate(s_t, 0)

        result = val.__le__(s)
        self.assertIs(result, NotImplemented)

    def test_ge_primitive_vs_struct_returns_not_implemented(self):
        class s_t(struct):
            x: c_int

        memory = bytearray(4)
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        s = lib.inflate(s_t, 0)

        result = val.__ge__(s)
        self.assertIs(result, NotImplemented)

    def test_eq_primitive_vs_struct_returns_not_implemented(self):
        class s_t(struct):
            x: c_int

        memory = bytearray(4)
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        s = lib.inflate(s_t, 0)

        result = val.__eq__(s)
        self.assertIs(result, NotImplemented)

    def test_ne_primitive_vs_struct_returns_not_implemented(self):
        class s_t(struct):
            x: c_int

        memory = bytearray(4)
        lib = inflater(memory)
        val = lib.inflate(c_int, 0)
        s = lib.inflate(s_t, 0)

        result = val.__ne__(s)
        self.assertIs(result, NotImplemented)

    def test_lt_between_compatible_primitives_works(self):
        """Comparisons between compatible primitives should still work."""
        memory = bytearray(8)
        lib = inflater(memory)
        a = lib.inflate(c_int, 0)
        b = lib.inflate(c_int, 4)
        a.value = 1
        b.value = 2

        self.assertTrue(a < b)
        self.assertFalse(b < a)

    def test_comparison_with_raw_int(self):
        memory = bytearray(4)
        lib = inflater(memory)
        a = lib.inflate(c_int, 0)
        a.value = 5

        self.assertTrue(a < 10)
        self.assertTrue(a > 2)
        self.assertTrue(a <= 5)
        self.assertTrue(a >= 5)


class NegativeArrayCountTest(unittest.TestCase):
    """array[T, N] must reject non-positive counts at handler time."""

    def test_negative_count_raises(self):
        """array[c_int, -5] must raise ValueError."""
        with self.assertRaises(ValueError):
            class s_t(struct):
                data: array[c_int, -5]
            # Force size computation
            size_of(s_t)

    def test_zero_count_raises(self):
        """array[c_int, 0] must raise ValueError."""
        with self.assertRaises(ValueError):
            class s_t(struct):
                data: array[c_int, 0]
            size_of(s_t)

    def test_positive_count_works(self):
        """array[c_int, 3] must work fine."""
        class s_t(struct):
            data: array[c_int, 3]
        self.assertEqual(size_of(s_t), 12)


class BitfieldFreezeSafetyTest(unittest.TestCase):
    """Frozen bitfields must reject writes even for non-owners."""

    def test_non_owner_bitfield_rejects_write_after_freeze(self):
        """The second bitfield in a group (non-owner) must reject writes when frozen."""
        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 1)
            b: c_uint = bitfield_of(c_uint, 1)

        memory = bytearray(4)
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)

        s.a.value = 1
        s.b.value = 1

        # Freeze the entire struct (which freezes all members)
        s.freeze()

        # Both bitfields should reject writes
        with self.assertRaises(ValueError):
            s.a.value = 0

        with self.assertRaises(ValueError):
            s.b.value = 0

    def test_individually_frozen_non_owner_rejects_write(self):
        """Freezing a non-owner bitfield individually must also reject writes."""
        class s_t(struct):
            a: c_uint = bitfield_of(c_uint, 1)
            b: c_uint = bitfield_of(c_uint, 1)

        memory = bytearray(4)
        lib = inflater(memory)
        s = lib.inflate(s_t, 0)

        s.b.value = 1

        # Freeze only the non-owner bitfield b
        s.b.freeze()

        with self.assertRaises(ValueError):
            s.b.value = 0


class TypeRegistryDeduplicationTest(unittest.TestCase):
    """Repeated handler registration must not accumulate duplicates."""

    def test_generic_handler_not_duplicated(self):
        """Registering the same handler twice must not produce duplicate entries."""
        from libdestruct.common.type_registry import TypeRegistry

        registry = TypeRegistry()

        class DummyType:
            pass

        def dummy_handler(item, args, owner):
            return None

        initial_count = len(registry.generic_handlers.get(DummyType, []))

        registry.register_generic_handler(DummyType, dummy_handler)
        registry.register_generic_handler(DummyType, dummy_handler)

        count = len(registry.generic_handlers[DummyType])
        self.assertEqual(count, initial_count + 1)

    def test_instance_handler_not_duplicated(self):
        """Registering the same instance handler twice must not produce duplicate entries."""
        from libdestruct.common.type_registry import TypeRegistry

        registry = TypeRegistry()

        class DummyField:
            pass

        def dummy_handler(item, annotation, owner):
            return None

        initial_count = len(registry.instance_handlers.get(DummyField, []))

        registry.register_instance_handler(DummyField, dummy_handler)
        registry.register_instance_handler(DummyField, dummy_handler)

        count = len(registry.instance_handlers[DummyField])
        self.assertEqual(count, initial_count + 1)

    def test_type_handler_not_duplicated(self):
        """Registering the same type handler twice must not produce duplicate entries."""
        from libdestruct.common.type_registry import TypeRegistry

        registry = TypeRegistry()

        class DummyParent:
            pass

        def dummy_handler(item):
            return None

        initial_count = len(registry.type_handlers.get(DummyParent, []))

        registry.register_type_handler(DummyParent, dummy_handler)
        registry.register_type_handler(DummyParent, dummy_handler)

        count = len(registry.type_handlers[DummyParent])
        self.assertEqual(count, initial_count + 1)


class ForwardTypedefTest(unittest.TestCase):
    """Forward typedef references are a known parser limitation."""

    def setUp(self):
        clear_parser_cache()

    def tearDown(self):
        clear_parser_cache()

    def test_chained_typedefs_in_order(self):
        """Chained typedefs in declaration order must work."""
        t = definition_to_type("""
            typedef unsigned int u32;
            typedef u32 mytype;
            struct S { mytype x; };
        """)
        data = (42).to_bytes(4, "little")
        s = t.from_bytes(data)
        self.assertEqual(s.x.value, 42)

    def test_forward_typedef_reference_raises(self):
        """Forward typedef reference (use before define) must raise a clear error, not crash."""
        with self.assertRaises((ValueError, TypeError)):
            definition_to_type("""
                typedef mytype1 mytype2;
                typedef unsigned int mytype1;
                struct S { mytype2 x; };
            """)


if __name__ == "__main__":
    unittest.main()
