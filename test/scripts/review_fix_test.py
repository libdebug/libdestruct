#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

"""Tests that expose bugs found during code review of the dev branch."""

import struct as pystruct
import unittest

from libdestruct import c_float, c_double, c_int, c_long, inflater, struct
from libdestruct.common.union import union, union_of


class EndiannessValidationTest(unittest.TestCase):
    """inflater() should reject invalid endianness strings."""

    def test_invalid_endianness_raises(self):
        """Passing a typo like 'big-endian' must raise ValueError, not silently produce wrong results."""
        with self.assertRaises(ValueError):
            inflater(bytearray(4), endianness="big-endian")

    def test_invalid_endianness_typo(self):
        """A random typo must raise ValueError."""
        with self.assertRaises(ValueError):
            inflater(bytearray(4), endianness="typo")

    def test_valid_endianness_big(self):
        """'big' is accepted without error."""
        lib = inflater(bytearray(4), endianness="big")
        self.assertIsNotNone(lib)

    def test_valid_endianness_little(self):
        """'little' is accepted without error."""
        lib = inflater(bytearray(4), endianness="little")
        self.assertIsNotNone(lib)

    def test_from_bytes_invalid_endianness(self):
        """from_bytes with invalid endianness must raise ValueError."""
        with self.assertRaises(ValueError):
            c_int.from_bytes(b"\x00\x00\x00\x00", endianness="big-endian")


class StructAttributeCollisionTest(unittest.TestCase):
    """Struct members named after internal attributes must not break core methods."""

    def test_struct_with_frozen_field_to_bytes(self):
        """A struct with a field named '_frozen' must still serialize correctly after freeze."""
        # This field name collides with obj._frozen used in to_bytes()
        class s_t(struct):
            _frozen: c_int
            b: c_int

        memory = b""
        memory += (10).to_bytes(4, "little")
        memory += (20).to_bytes(4, "little")

        s = s_t.from_bytes(memory)
        # to_bytes must return the correct serialized data, not crash
        self.assertEqual(s.to_bytes(), memory)

    def test_struct_with_frozen_field_hexdump(self):
        """A struct with a '_frozen' field must still produce a hexdump."""
        class s_t(struct):
            _frozen: c_int

        s = s_t.from_bytes((42).to_bytes(4, "little"))
        # hexdump must not crash
        dump = s.hexdump()
        self.assertIn("2a", dump)

    def test_struct_with_members_field_eq(self):
        """A struct with a field named '_members' must still support equality."""
        class s_t(struct):
            _members: c_int

        a = s_t.from_bytes((1).to_bytes(4, "little"))
        b = s_t.from_bytes((1).to_bytes(4, "little"))
        self.assertEqual(a, b)

    def test_struct_with_members_field_to_dict(self):
        """A struct with a field named '_members' must still support to_dict."""
        class s_t(struct):
            _members: c_int

        s = s_t.from_bytes((5).to_bytes(4, "little"))
        d = s.to_dict()
        self.assertEqual(d["_members"], 5)

    def test_struct_with_frozen_struct_bytes_field(self):
        """A field named '_frozen_struct_bytes' must not break freeze/to_bytes."""
        class s_t(struct):
            _frozen_struct_bytes: c_int

        memory = (99).to_bytes(4, "little")
        s = s_t.from_bytes(memory)
        self.assertEqual(s.to_bytes(), memory)


class UnionGetAttrSafetyTest(unittest.TestCase):
    """union.__getattr__ must produce clear errors, not internal AttributeError."""

    def test_missing_attribute_error_message(self):
        """Accessing a nonexistent attribute on a union should mention the attribute name, not '_variants'."""
        u = union(None, None, 4)
        with self.assertRaises(AttributeError) as ctx:
            _ = u.nonexistent_attr
        # The error message must mention the user's attribute, not internal implementation details
        self.assertIn("nonexistent_attr", str(ctx.exception))
        self.assertNotIn("_variants", str(ctx.exception))

    def test_getattr_after_del_variants(self):
        """Even if _variants is somehow missing, __getattr__ should not expose internal details."""
        u = union(None, None, 4)
        del u.__dict__["_variants"]
        with self.assertRaises(AttributeError) as ctx:
            _ = u.something
        self.assertIn("something", str(ctx.exception))


class FloatDuplicationRegressionTest(unittest.TestCase):
    """After refactoring c_float/c_double to a shared base, core behavior must be preserved."""

    def test_c_float_read_write(self):
        memory = bytearray(4)
        lib = inflater(memory)
        f = lib.inflate(c_float, 0)
        f.value = 3.14
        self.assertAlmostEqual(f.value, 3.14, places=5)

    def test_c_double_read_write(self):
        memory = bytearray(8)
        lib = inflater(memory)
        d = lib.inflate(c_double, 0)
        d.value = 2.718281828
        self.assertAlmostEqual(d.value, 2.718281828, places=8)

    def test_c_float_freeze_diff_reset(self):
        memory = bytearray(4)
        lib = inflater(memory)
        f = lib.inflate(c_float, 0)
        f.value = 1.5
        f.freeze()
        self.assertAlmostEqual(f.value, 1.5, places=5)
        with self.assertRaises(ValueError):
            f.value = 2.0

    def test_c_double_freeze_diff_reset(self):
        memory = bytearray(8)
        lib = inflater(memory)
        d = lib.inflate(c_double, 0)
        d.value = 1.5
        d.freeze()
        self.assertAlmostEqual(d.value, 1.5, places=5)
        with self.assertRaises(ValueError):
            d.value = 2.0

    def test_c_float_from_bytes(self):
        data = pystruct.pack("<f", 42.0)
        f = c_float.from_bytes(data)
        self.assertAlmostEqual(f.value, 42.0, places=5)

    def test_c_double_from_bytes(self):
        data = pystruct.pack("<d", 42.0)
        d = c_double.from_bytes(data)
        self.assertAlmostEqual(d.value, 42.0, places=8)

    def test_c_float_int_conversion(self):
        data = pystruct.pack("<f", 3.7)
        f = c_float.from_bytes(data)
        self.assertEqual(int(f), 3)

    def test_c_double_int_conversion(self):
        data = pystruct.pack("<d", 3.7)
        d = c_double.from_bytes(data)
        self.assertEqual(int(d), 3)

    def test_c_float_to_bytes_round_trip(self):
        original = pystruct.pack("<f", 1.5)
        f = c_float.from_bytes(original)
        self.assertEqual(f.to_bytes(), original)

    def test_c_double_to_bytes_round_trip(self):
        original = pystruct.pack("<d", 1.5)
        d = c_double.from_bytes(original)
        self.assertEqual(d.to_bytes(), original)

    def test_c_float_size(self):
        self.assertEqual(c_float.size, 4)

    def test_c_double_size(self):
        self.assertEqual(c_double.size, 8)

    def test_c_float_big_endian(self):
        original = pystruct.pack(">f", 3.14)
        f = c_float.from_bytes(original, endianness="big")
        self.assertAlmostEqual(f.value, 3.14, places=5)
        self.assertEqual(f.to_bytes(), original)

    def test_c_double_big_endian(self):
        original = pystruct.pack(">d", 2.718)
        d = c_double.from_bytes(original, endianness="big")
        self.assertAlmostEqual(d.value, 2.718, places=3)
        self.assertEqual(d.to_bytes(), original)


if __name__ == "__main__":
    unittest.main()
