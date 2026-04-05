#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import struct as pystruct
import unittest
from enum import IntEnum, IntFlag

from libdestruct import struct, c_int, c_short, inflater, size_of
from libdestruct.common.flags import flags, flags_of


class Perms(IntFlag):
    READ = 4
    WRITE = 2
    EXEC = 1


class FlagsTest(unittest.TestCase):
    """Bit flags tests."""

    def test_single_flag(self):
        """One flag bit set returns correct IntFlag member."""
        data = pystruct.pack("<i", 4)
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(flags[Perms], 0)
        self.assertEqual(f.get(), Perms.READ)

    def test_combined_flags(self):
        """Multiple bits set returns combined IntFlag value."""
        data = pystruct.pack("<i", 6)  # READ | WRITE
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(flags[Perms], 0)
        result = f.get()
        self.assertIn(Perms.READ, result)
        self.assertIn(Perms.WRITE, result)
        self.assertNotIn(Perms.EXEC, result)

    def test_no_flags(self):
        """Zero value returns IntFlag(0)."""
        data = pystruct.pack("<i", 0)
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(flags[Perms], 0)
        self.assertEqual(f.get(), Perms(0))

    def test_all_flags(self):
        """All bits set returns correct combination."""
        data = pystruct.pack("<i", 7)  # READ | WRITE | EXEC
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(flags[Perms], 0)
        result = f.get()
        self.assertIn(Perms.READ, result)
        self.assertIn(Perms.WRITE, result)
        self.assertIn(Perms.EXEC, result)

    def test_flags_in_struct_descriptor(self):
        """flags_of(Perms) as struct field default value."""
        class file_t(struct):
            mode: flags = flags_of(Perms)

        data = pystruct.pack("<i", 5)  # READ | EXEC
        f = file_t.from_bytes(data)
        result = f.mode.get()
        self.assertIn(Perms.READ, result)
        self.assertIn(Perms.EXEC, result)

    def test_flags_in_struct_subscript(self):
        """flags[Perms] as struct field annotation."""
        class file_t(struct):
            mode: flags[Perms]

        data = pystruct.pack("<i", 3)  # WRITE | EXEC
        f = file_t.from_bytes(data)
        result = f.mode.get()
        self.assertIn(Perms.WRITE, result)
        self.assertIn(Perms.EXEC, result)

    def test_flags_custom_backing(self):
        """flags[Perms, c_short] uses 2-byte backing."""
        class file_t(struct):
            mode: flags[Perms, c_short]

        self.assertEqual(size_of(file_t), 2)
        data = pystruct.pack("<h", 4)
        f = file_t.from_bytes(data)
        self.assertEqual(f.mode.get(), Perms.READ)

    def test_flags_write(self):
        """Write combined value via .value."""
        memory = bytearray(4)
        lib = inflater(memory)

        class file_t(struct):
            mode: flags[Perms]

        f = lib.inflate(file_t, 0)
        f.mode.value = Perms.READ | Perms.EXEC
        self.assertEqual(f.mode.get(), Perms.READ | Perms.EXEC)

    def test_flags_lenient_unknown(self):
        """Unknown bits in lenient mode return raw int."""
        data = pystruct.pack("<i", 0xFF)  # has bits beyond defined flags
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(flags[Perms], 0)
        result = f.get()
        # In lenient mode, IntFlag handles unknown bits gracefully
        self.assertIsNotNone(result)

    def test_flags_strict_unknown(self):
        """Unknown bits in strict mode raise ValueError."""
        class file_t(struct):
            mode: flags = flags_of(Perms, lenient=False)

        data = pystruct.pack("<i", 0xFF)
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(file_t, 0)
        with self.assertRaises(ValueError):
            f.mode.get()

    def test_flags_round_trip(self):
        """from_bytes -> to_bytes identity."""
        data = pystruct.pack("<i", 5)
        f = flags[Perms]
        memory = bytearray(data)
        lib = inflater(memory)
        obj = lib.inflate(f, 0)
        self.assertEqual(obj.to_bytes(), data)

    def test_flags_to_str(self):
        """to_str() returns readable representation."""
        data = pystruct.pack("<i", 5)
        memory = bytearray(data)
        lib = inflater(memory)
        f = lib.inflate(flags[Perms], 0)
        s = f.to_str()
        self.assertIsInstance(s, str)
        self.assertTrue(len(s) > 0)

    def test_flags_rejects_non_intflag(self):
        """flags_of(IntEnum) raises TypeError."""
        class Color(IntEnum):
            RED = 1

        with self.assertRaises(TypeError):
            flags_of(Color)

    def test_size_of_flags(self):
        """size_of(flags[Perms]) returns 4."""
        self.assertEqual(size_of(flags[Perms]), 4)


if __name__ == "__main__":
    unittest.main()
