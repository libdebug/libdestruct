#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
# Tests that verify bugs found during code review.
# Each test is expected to FAIL on the current dev branch.
#

import struct as pystruct
import unittest

from libdestruct import (
    c_char,
    c_int,
    c_long,
    c_short,
    inflater,
    ptr,
    ptr_to,
    size_of,
    struct,
    tagged_union,
    union_of,
)
from libdestruct.backing.memory_resolver import MemoryResolver
from libdestruct.common.union.union import union
from libdestruct.common.union.union_field import UnionField
from libdestruct.common.union.tagged_union_field import TaggedUnionField
from libdestruct.common.utils import alignment_of


class Bug1_AlignedStructTailPaddingInstance(unittest.TestCase):
    """Bug: _inflate_struct_attributes does not apply tail padding for aligned structs.

    compute_own_size (class-level) correctly adds tail padding so that
    size_of(aligned_t) == 8, but _inflate_struct_attributes (instance-level)
    sets self.size = current_offset without tail padding, giving size 5.

    This means size_of(instance) != size_of(class) for aligned structs
    where the last field doesn't end on an aligned boundary.
    """

    def test_instance_size_matches_class_size(self):
        """size_of(instance) should equal size_of(class) for aligned structs."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_int    # 4 bytes at offset 0
            b: c_char   # 1 byte at offset 4, then 3 bytes tail padding

        # Class size correctly includes tail padding
        self.assertEqual(size_of(aligned_t), 8)

        memory = pystruct.pack("<ib", 42, 0x41) + b"\x00" * 3
        s = aligned_t.from_bytes(memory)

        # Instance size should also be 8 (with tail padding), not 5
        self.assertEqual(size_of(s), 8)

    def test_to_bytes_includes_tail_padding(self):
        """to_bytes() should return 8 bytes (including tail padding), not 5."""
        class aligned_t(struct):
            _aligned_ = True
            a: c_int    # 4 bytes
            b: c_char   # 1 byte + 3 bytes tail padding

        memory = pystruct.pack("<ib", 42, 0x41) + b"\x00" * 3
        s = aligned_t.from_bytes(memory)

        # to_bytes uses size_of(self) which should be 8
        self.assertEqual(len(s.to_bytes()), 8)

    def test_nested_aligned_struct_tail_padding(self):
        """Nested aligned structs should also have correct tail padding."""
        class inner_t(struct):
            _aligned_ = True
            x: c_int    # 4 bytes
            y: c_char   # 1 byte + 3 tail padding = 8 total

        class outer_t(struct):
            _aligned_ = True
            a: inner_t
            b: c_int    # should start at offset 8, not 5

        self.assertEqual(size_of(inner_t), 8)

        memory = b"\x00" * 16
        s = outer_t.from_bytes(memory)
        self.assertEqual(size_of(s), size_of(outer_t))


class Bug2_PtrUnwrapLengthZero(unittest.TestCase):
    """Bug: ptr.unwrap(0) reads 1 byte instead of 0 bytes.

    In ptr.py line 106: `result = target_resolver.resolve(length or 1, 0)`
    The `or 1` treats 0 as falsy, so unwrap(0) resolves 1 byte.
    Should use `length if length is not None else 1`.
    """

    def test_unwrap_length_zero_returns_empty(self):
        """unwrap(0) should return 0 bytes, not 1 byte."""
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")  # pointer value = 8
        memory[8] = 0xAB  # target byte

        p = ptr(MemoryResolver(memory, 0))

        result = p.unwrap(0)
        self.assertEqual(len(result), 0)
        self.assertEqual(result, b"")

    def test_unwrap_length_none_returns_one_byte(self):
        """unwrap() (default None) should still return 1 byte."""
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8] = 0xAB

        p = ptr(MemoryResolver(memory, 0))

        result = p.unwrap()
        self.assertEqual(len(result), 1)
        self.assertEqual(result, bytes([0xAB]))

    def test_try_unwrap_length_zero(self):
        """try_unwrap(0) should also return empty bytes, not 1 byte."""
        memory = bytearray(16)
        memory[0:8] = (8).to_bytes(8, "little")
        memory[8] = 0xAB

        p = ptr(MemoryResolver(memory, 0))

        result = p.try_unwrap(0)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)


class Bug3_CParserAnonymousStructCachedWithNoneKey(unittest.TestCase):
    """Bug: Anonymous structs are cached with None key in PARSED_STRUCTS.

    In struct_parser.py line 100: `PARSED_STRUCTS[root.name] = result`
    If root.name is None (anonymous struct), this stores result with key None,
    which means all anonymous structs overwrite each other in the cache.
    """

    def test_none_key_not_in_cache(self):
        """Anonymous struct should not pollute PARSED_STRUCTS with a None key."""
        from libdestruct.c.struct_parser import definition_to_type, PARSED_STRUCTS

        # Clear the cache to start fresh
        PARSED_STRUCTS.clear()

        definition_to_type("struct { int x; };")

        # None should not be a key in the cache
        self.assertNotIn(None, PARSED_STRUCTS)


class Bug4_CParserUnsizedArray(unittest.TestCase):
    """Bug: arr_to_type crashes on unsized arrays (e.g. int arr[]).

    In struct_parser.py line 173: `int(arr.dim.value)` crashes with
    AttributeError if arr.dim is None (unsized/flexible array member).
    """

    def test_unsized_array_member(self):
        """Parsing a struct with a flexible array member should not crash."""
        from libdestruct.c.struct_parser import definition_to_type

        # This should either parse successfully or raise a clear error,
        # not crash with AttributeError: 'NoneType' object has no attribute 'value'
        try:
            result = definition_to_type("struct test { int count; int data[]; };")
            # If it succeeds, verify it's a valid struct type
            self.assertTrue(hasattr(result, '__annotations__'))
        except (ValueError, TypeError) as e:
            # A clear error message is acceptable
            self.assertNotIn("AttributeError", str(type(e)))
        except AttributeError:
            self.fail("arr_to_type crashed with AttributeError on unsized array - should handle gracefully")


class Bug5_DocResolverParameterNames(unittest.TestCase):
    """Bug: Documentation uses wrong parameter names for Resolver methods.

    docs/memory/resolvers.md says:
      - resolve(size, offset) -- actual signature: resolve(size, index)
      - relative_from_own(offset, size) -- actual: relative_from_own(address_offset, index_offset)
    """

    def test_resolve_parameter_name_is_index(self):
        """Resolver.resolve second parameter should be 'index', not 'offset'."""
        from libdestruct.backing.resolver import Resolver
        import inspect

        sig = inspect.signature(Resolver.resolve)
        params = list(sig.parameters.keys())
        # params should be ['self', 'size', 'index']
        self.assertEqual(params[2], "index")

    def test_relative_from_own_parameter_names(self):
        """Resolver.relative_from_own parameters should be address_offset, index_offset."""
        from libdestruct.backing.resolver import Resolver
        import inspect

        sig = inspect.signature(Resolver.relative_from_own)
        params = list(sig.parameters.keys())
        # params should be ['self', 'address_offset', 'index_offset']
        self.assertEqual(params[1], "address_offset")
        self.assertEqual(params[2], "index_offset")


class Bug6_EnumSetFailsWithLenientRawInt(unittest.TestCase):
    """Bug: enum._set crashes when given a raw integer from lenient mode.

    In enum.py line 67: `self._backing_type.set(value.value)`
    When lenient=True and get() returns a raw int (no matching enum member),
    calling _set(raw_int) crashes because int has no .value attribute.
    """

    def test_set_raw_int_from_lenient_get(self):
        """Setting back a raw int obtained from lenient get() should work."""
        from enum import IntEnum
        from libdestruct.common.enum.enum import enum as ld_enum

        class Color(IntEnum):
            RED = 0
            GREEN = 1

        memory = bytearray((99).to_bytes(4, "little"))
        e = ld_enum(MemoryResolver(memory, 0), Color, c_int, lenient=True)

        # get() returns raw int in lenient mode
        val = e.get()
        self.assertEqual(val, 99)
        self.assertIsInstance(val, int)
        self.assertNotIsInstance(val, IntEnum)

        # Setting it back should work, not crash with AttributeError
        e.value = val
        self.assertEqual(e.get(), 99)

    def test_set_enum_member_still_works(self):
        """Setting a valid enum member should still work."""
        from enum import IntEnum
        from libdestruct.common.enum.enum import enum as ld_enum

        class Color(IntEnum):
            RED = 0
            GREEN = 1

        memory = bytearray(4)
        e = ld_enum(MemoryResolver(memory, 0), Color, c_int, lenient=True)

        e.value = Color.GREEN
        self.assertEqual(e.get(), Color.GREEN)

    def test_reset_after_freeze_with_unknown_value(self):
        """freeze() + reset() with unknown enum value should not crash."""
        from enum import IntEnum
        from libdestruct.common.enum.enum import enum as ld_enum

        class Color(IntEnum):
            RED = 0
            GREEN = 1

        memory = bytearray((99).to_bytes(4, "little"))
        e = ld_enum(MemoryResolver(memory, 0), Color, c_int, lenient=True)

        e.freeze()
        memory[0:4] = (0).to_bytes(4, "little")

        # reset() calls _set(frozen_value) where frozen_value is raw int 99
        e.reset()
        self.assertEqual(e.get(), 99)


class _aligned_plain_union_t(struct):
    _aligned_ = True
    tag: c_char
    data: union = union_of({"i": c_int, "c": c_char})


class _aligned_tagged_union_t(struct):
    _aligned_ = True
    type: c_char
    payload: union = tagged_union("type", {0: c_int})


class Bug7_UnionAlignmentInInstances(unittest.TestCase):
    """Bug: union/tagged_union fields get wrong offsets in aligned struct instances.

    During inflation, union_field_inflater and tagged_union_field_inflater
    return closures that alignment_of() can't inspect, so it returns 1
    instead of the correct alignment. This means union fields in aligned
    structs are placed at the wrong offset.

    compute_own_size works around this by creating a stub instance
    (resolved_type(None)) and checking its alignment, but
    _inflate_struct_attributes doesn't.
    """

    def test_plain_union_alignment(self):
        """Plain union should be aligned to its max member alignment."""
        memory = bytearray(8)
        memory[0] = 0x41
        memory[4:8] = (42).to_bytes(4, "little")  # c_int at offset 4

        lib = inflater(memory)
        s = lib.inflate(_aligned_plain_union_t, 0)
        offsets = object.__getattribute__(s, "_member_offsets")

        # Union should be at offset 4 (aligned to c_int alignment), not offset 1
        self.assertEqual(offsets["data"], 4)
        self.assertEqual(s.data.i.value, 42)

    def test_tagged_union_alignment(self):
        """Tagged union should also be aligned correctly."""
        memory = bytearray(8)
        memory[0] = 0      # type = 0
        memory[4:8] = (42).to_bytes(4, "little")  # payload at aligned offset

        lib = inflater(memory)
        s = lib.inflate(_aligned_tagged_union_t, 0)
        offsets = object.__getattribute__(s, "_member_offsets")

        # Payload should be at offset 4, not offset 1
        self.assertEqual(offsets["payload"], 4)
        self.assertEqual(s.payload.value, 42)


class Bug8_ArrayFreezeDoesNotFreezeElements(unittest.TestCase):
    """Bug: Freezing a struct with an array doesn't freeze the array elements.

    array_impl inherits obj.freeze(), which stores self.get() (a list of
    newly-created element objects backed by the live resolver). But those
    elements are never themselves frozen, and array_impl.__getitem__ creates
    fresh elements from the live resolver, completely bypassing the frozen state.

    This means:
    - s.data[0].value returns live data after freeze + memory mutation
    - s.data.value returns a list of live-backed element objects
    - s.data.to_bytes() returns live bytes
    Only s.to_bytes() (which uses _frozen_struct_bytes) returns correct frozen data.
    """

    def test_array_element_access_returns_frozen_value(self):
        """s.data[0].value should return the frozen value, not live memory."""
        from libdestruct import inflater, array_of

        class arr_struct_t(struct):
            count: c_int
            data: array_of(c_int, 3)

        memory = bytearray(16)
        memory[0:4] = (3).to_bytes(4, "little")    # count = 3
        memory[4:8] = (10).to_bytes(4, "little")    # data[0] = 10
        memory[8:12] = (20).to_bytes(4, "little")   # data[1] = 20
        memory[12:16] = (30).to_bytes(4, "little")  # data[2] = 30

        lib = inflater(memory)
        s = lib.inflate(arr_struct_t, 0)
        s.freeze()

        # Mutate underlying memory
        memory[4:8] = (99).to_bytes(4, "little")  # data[0] = 99 in live memory

        # Primitive field correctly returns frozen value
        self.assertEqual(s.count.value, 3)

        # Array element should also return frozen value (10), not live (99)
        self.assertEqual(s.data[0].value, 10)

    def test_array_value_property_returns_frozen_elements(self):
        """s.data.value should contain frozen element values after memory mutation."""
        from libdestruct import inflater, array_of

        class arr_struct_t(struct):
            data: array_of(c_int, 2)

        memory = bytearray(8)
        memory[0:4] = (10).to_bytes(4, "little")
        memory[4:8] = (20).to_bytes(4, "little")

        lib = inflater(memory)
        s = lib.inflate(arr_struct_t, 0)
        s.freeze()

        memory[0:4] = (99).to_bytes(4, "little")

        # The frozen list's elements should reflect the frozen state
        frozen_vals = [elem.value for elem in s.data.value]
        self.assertEqual(frozen_vals, [10, 20])

    def test_array_to_bytes_returns_frozen_bytes(self):
        """s.data.to_bytes() should return frozen bytes, not live memory."""
        from libdestruct import inflater, array_of

        class arr_struct_t(struct):
            data: array_of(c_int, 2)

        memory = bytearray(8)
        memory[0:4] = (10).to_bytes(4, "little")
        memory[4:8] = (20).to_bytes(4, "little")

        lib = inflater(memory)
        s = lib.inflate(arr_struct_t, 0)
        s.freeze()

        expected_bytes = bytes(memory)  # capture before mutation

        memory[0:4] = (99).to_bytes(4, "little")

        self.assertEqual(s.data.to_bytes(), expected_bytes)


if __name__ == "__main__":
    unittest.main()
