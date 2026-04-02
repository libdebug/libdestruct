#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest

from libdestruct import struct, c_char, c_int, c_long, inflater, size_of, alignment_of


class base_t(struct):
    a: c_int


class derived_t(base_t):
    b: c_int


class level_a(struct):
    x: c_int


class level_b(level_a):
    y: c_int


class level_c(level_b):
    z: c_int


class InheritanceTest(unittest.TestCase):
    """Struct inheritance tests."""

    def test_basic_inheritance_fields(self):
        """Derived struct has both parent and own fields."""
        data = pystruct.pack("<ii", 10, 20)
        d = derived_t.from_bytes(data)
        self.assertEqual(d.a.value, 10)
        self.assertEqual(d.b.value, 20)

    def test_basic_inheritance_size(self):
        """size_of(derived_t) includes parent fields."""
        self.assertEqual(size_of(derived_t), 8)

    def test_size_of_derived_after_base(self):
        """Bug test: size_of(base) then size_of(derived) must both be correct."""
        self.assertEqual(size_of(base_t), 4)
        self.assertEqual(size_of(derived_t), 8)

    def test_alignment_of_derived_after_base(self):
        """Bug test: alignment_of must not leak parent's _type_impl."""
        class aligned_base(struct):
            _aligned_ = True
            a: c_int

        class aligned_derived(aligned_base):
            b: c_long

        # Inflate base first
        alignment_of(aligned_base)
        # derived should compute its own alignment (8 from c_long), not reuse base's (4)
        self.assertEqual(alignment_of(aligned_derived), 8)

    def test_multi_level_inheritance(self):
        """Three-level chain A -> B -> C, each adding c_int."""
        self.assertEqual(size_of(level_c), 12)
        data = pystruct.pack("<iii", 1, 2, 3)
        c = level_c.from_bytes(data)
        self.assertEqual(c.x.value, 1)
        self.assertEqual(c.y.value, 2)
        self.assertEqual(c.z.value, 3)

    def test_inheritance_field_order(self):
        """Parent fields come first in to_dict()."""
        data = pystruct.pack("<iii", 10, 20, 30)
        c = level_c.from_bytes(data)
        d = c.to_dict()
        keys = list(d.keys())
        self.assertEqual(keys, ["x", "y", "z"])

    def test_inherited_keyword_init(self):
        """Keyword init works with inherited fields."""
        d = derived_t(a=10, b=20)
        self.assertEqual(d.a.value, 10)
        self.assertEqual(d.b.value, 20)

    def test_inherited_from_bytes_round_trip(self):
        """to_bytes / from_bytes round-trip preserves data."""
        data = pystruct.pack("<ii", 42, 99)
        d1 = derived_t.from_bytes(data)
        raw = d1.to_bytes()
        d2 = derived_t.from_bytes(raw)
        self.assertEqual(d2.a.value, 42)
        self.assertEqual(d2.b.value, 99)

    def test_inheritance_with_alignment(self):
        """Aligned base, derived adds c_long. Alignment should be 8."""
        class aligned_base(struct):
            _aligned_ = True
            a: c_char
            b: c_int

        class aligned_derived(aligned_base):
            c: c_long

        self.assertEqual(alignment_of(aligned_derived), 8)
        self.assertEqual(size_of(aligned_derived), 16)  # 1+3pad+4+8

    def test_inherited_to_str(self):
        """to_str() shows all inherited fields."""
        data = pystruct.pack("<ii", 10, 20)
        d = derived_t.from_bytes(data)
        s = d.to_str()
        self.assertIn("a:", s)
        self.assertIn("b:", s)

    def test_inherited_equality(self):
        """Two derived instances with same data are equal."""
        data = pystruct.pack("<ii", 10, 20)
        d1 = derived_t.from_bytes(data)
        d2 = derived_t.from_bytes(data)
        self.assertEqual(d1, d2)

    def test_base_and_derived_independent(self):
        """Inflating derived does not corrupt base's size."""
        self.assertEqual(size_of(base_t), 4)
        self.assertEqual(size_of(derived_t), 8)
        self.assertEqual(size_of(base_t), 4)  # still 4


if __name__ == "__main__":
    unittest.main()
