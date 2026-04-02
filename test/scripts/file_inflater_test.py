#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import mmap
import os
import struct as pystruct
import tempfile
import unittest

from libdestruct import struct, c_int, c_long, inflater, inflater_from_file, size_of


class point_t(struct):
    x: c_int
    y: c_int


class FileInflaterTest(unittest.TestCase):
    """File-backed inflater tests."""

    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(delete=False)
        self.tmpfile.write(pystruct.pack("<ii", 10, 20))
        self.tmpfile.flush()
        self.tmppath = self.tmpfile.name

    def tearDown(self):
        self.tmpfile.close()
        os.unlink(self.tmppath)

    def test_inflater_accepts_mmap(self):
        """inflater() should accept mmap objects without raising TypeError."""
        with mmap.mmap(self.tmpfile.fileno(), 0, access=mmap.ACCESS_READ) as m:
            lib = inflater(m)
            self.assertIsNotNone(lib)

    def test_inflate_struct_from_mmap(self):
        """Read struct fields from mmap-backed inflater."""
        with mmap.mmap(self.tmpfile.fileno(), 0, access=mmap.ACCESS_READ) as m:
            lib = inflater(m)
            p = lib.inflate(point_t, 0)
            self.assertEqual(p.x.value, 10)
            self.assertEqual(p.y.value, 20)

    def test_write_to_mmap(self):
        """Write value via mmap-backed inflater, verify it persists."""
        with mmap.mmap(self.tmpfile.fileno(), 0, access=mmap.ACCESS_WRITE) as m:
            lib = inflater(m)
            p = lib.inflate(point_t, 0)
            p.x.value = 42
            self.assertEqual(p.x.value, 42)
            # Verify the mmap itself was updated
            self.assertEqual(pystruct.unpack("<i", m[0:4])[0], 42)

    def test_inflater_from_file_reads(self):
        """inflater_from_file inflates a struct correctly."""
        with inflater_from_file(self.tmppath) as lib:
            p = lib.inflate(point_t, 0)
            self.assertEqual(p.x.value, 10)
            self.assertEqual(p.y.value, 20)

    def test_inflater_from_file_context_manager(self):
        """Context manager cleans up resources."""
        with inflater_from_file(self.tmppath) as lib:
            p = lib.inflate(point_t, 0)
            self.assertEqual(p.x.value, 10)
        # After exiting, the file inflater should have closed its resources
        self.assertTrue(lib._mmap.closed)

    def test_inflater_from_file_writable(self):
        """writable=True allows writing back to the file."""
        with inflater_from_file(self.tmppath, writable=True) as lib:
            p = lib.inflate(point_t, 0)
            p.x.value = 99

        # Re-read the file to confirm the write persisted
        with open(self.tmppath, "rb") as f:
            data = f.read()
        self.assertEqual(pystruct.unpack("<ii", data), (99, 20))

    def test_inflater_from_file_multiple_offsets(self):
        """Inflate multiple structs at different offsets."""
        # Write two points
        self.tmpfile.seek(0)
        self.tmpfile.write(pystruct.pack("<iiii", 1, 2, 3, 4))
        self.tmpfile.flush()

        with inflater_from_file(self.tmppath) as lib:
            p1 = lib.inflate(point_t, 0)
            p2 = lib.inflate(point_t, 8)
            self.assertEqual(p1.x.value, 1)
            self.assertEqual(p1.y.value, 2)
            self.assertEqual(p2.x.value, 3)
            self.assertEqual(p2.y.value, 4)

    def test_inflater_rejects_non_sequence(self):
        """inflater(42) still raises TypeError."""
        with self.assertRaises(TypeError):
            inflater(42)


if __name__ == "__main__":
    unittest.main()
