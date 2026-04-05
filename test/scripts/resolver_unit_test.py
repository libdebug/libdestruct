#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdestruct import c_int, c_str, c_uint, inflater, struct, ptr, ptr_to_self
from libdestruct.backing.fake_resolver import FakeResolver
from libdestruct.backing.memory_resolver import MemoryResolver


class FakeResolverTest(unittest.TestCase):
    def test_resolve_default_page_with_offset(self):
        """FakeResolver.resolve() should return zero-filled bytes for non-existent pages regardless of offset."""
        resolver = FakeResolver()
        resolver.address = 0x800

        data = resolver.resolve(4, 0)
        self.assertEqual(len(data), 4)
        self.assertEqual(data, b"\x00\x00\x00\x00")

    def test_read_spanning_page_boundary(self):
        resolver = FakeResolver()
        resolver.address = 0xFFE  # 2 bytes before page boundary

        data = resolver.resolve(8, 0)
        self.assertEqual(len(data), 8)
        self.assertEqual(data, b"\x00" * 8)

    def test_read_with_populated_page(self):
        resolver = FakeResolver()
        page = b"\xAA" * 0x1000
        resolver.memory[0x0] = page
        resolver.address = 0x10

        data = resolver.resolve(4, 0)
        self.assertEqual(data, b"\xAA" * 4)

    def test_write_then_read_cross_page(self):
        resolver = FakeResolver()
        resolver.address = 0xFFE

        resolver.modify(4, 0, b"\x01\x02\x03\x04")
        data = resolver.resolve(4, 0)
        self.assertEqual(data, b"\x01\x02\x03\x04")


class MemoryResolverTest(unittest.TestCase):
    def test_resolve_returns_bytes_not_bytearray(self):
        """MemoryResolver.resolve() must return bytes even when backing is bytearray."""
        resolver = MemoryResolver(bytearray(b"\x01\x02\x03\x04"), 0)
        result = resolver.resolve(4, 0)
        self.assertIsInstance(result, bytes)

    def test_bytes_on_bytearray_backed_c_int(self):
        lib = inflater(bytearray(b"\x2a\x00\x00\x00"))
        obj = lib.inflate(c_int, 0)

        result = bytes(obj)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 4)

    def test_bytes_on_bytearray_backed_c_str(self):
        lib = inflater(bytearray(b"Hello\x00"))
        s = lib.inflate(c_str, 0)

        result = bytes(s)
        self.assertIsInstance(result, bytes)

    def test_bytes_on_bytearray_backed_ptr(self):
        class test_t(struct):
            p: ptr = ptr_to_self()

        memory = bytearray(b"\x00" * 8)
        test = test_t.from_bytes(memory)

        result = test.p.to_bytes()
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 8)

    def test_c_str_get_returns_bytes(self):
        lib = inflater(bytearray(b"Hello\x00"))
        s = lib.inflate(c_str, 0)

        result = s.get()
        self.assertIsInstance(result, bytes)

        result = s.get(0)
        self.assertIsInstance(result, bytes)

    def test_write_to_bytearray_memory(self):
        memory = bytearray(b"\x00" * 8)
        lib = inflater(memory)
        obj = lib.inflate(c_int, 0)

        obj.value = 0x7EADBEEF
        self.assertEqual(obj.value, 0x7EADBEEF)

    def test_c_uint_write_to_bytearray(self):
        memory = bytearray(b"\x00" * 4)
        lib = inflater(memory)
        obj = lib.inflate(c_uint, 0)

        obj.value = 0xDEADBEEF
        self.assertEqual(obj.value, 0xDEADBEEF)


if __name__ == "__main__":
    unittest.main()
