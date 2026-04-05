#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest
from enum import IntEnum

from libdestruct import c_int, inflater, struct, array_of, enum, enum_of


class ArrayUnitTest(unittest.TestCase):
    """Array operations without debugger."""

    def test_array_value_property(self):
        """.value calls self.get() without args - should not raise TypeError."""
        memory = b"".join((i).to_bytes(4, "little") for i in range(5))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 5), 0)

        val = arr.value
        self.assertIsNotNone(val)

    def test_array_repr(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(3))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)

        r = repr(arr)
        self.assertIsInstance(r, str)

    def test_array_indexing(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(5))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 5), 0)

        for i in range(5):
            self.assertEqual(arr[i].value, i)

    def test_array_iteration(self):
        memory = b"".join((i * 10).to_bytes(4, "little") for i in range(3))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)

        values = [x.value for x in arr]
        self.assertEqual(values, [0, 10, 20])

    def test_array_len(self):
        memory = b"".join((0).to_bytes(4, "little") for _ in range(7))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 7), 0)

        self.assertEqual(len(arr), 7)

    def test_array_contains(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(5))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 5), 0)

        elem = arr[2]
        self.assertIn(elem, arr)

    def test_array_to_bytes(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(3))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)

        result = arr.to_bytes()
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, memory)

    def test_array_to_str(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(3))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)

        result = arr.to_str()
        self.assertIn("0", result)
        self.assertIn("1", result)
        self.assertIn("2", result)

    def test_array_value_returns_all_elements(self):
        memory = b"".join((i).to_bytes(4, "little") for i in range(4))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 4), 0)

        val = arr.value
        self.assertIsInstance(val, list)
        self.assertEqual(len(val), 4)
        self.assertEqual([x.value for x in val], [0, 1, 2, 3])

    def test_bytes_on_bytearray_backed_array(self):
        memory = bytearray(b"".join((i).to_bytes(4, "little") for i in range(3)))
        lib = inflater(memory)
        arr = lib.inflate(array_of(c_int, 3), 0)

        result = bytes(arr)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 12)


if __name__ == "__main__":
    unittest.main()
