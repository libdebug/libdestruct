#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdebug import debugger
from libdestruct import inflater, c_int, c_long, c_uint, c_ulong

class BasicTest(unittest.TestCase):
    def test_integer_types(self):
        d = debugger("binaries/basic_test")

        d.run()

        # Validate readings
        bp1 = d.bp("signpost2")

        # Validate assignments
        bp2 = d.bp("signpost3")

        libdestruct = inflater(d.memory)

        d.cont()

        self.assertTrue(bp1.hit_on(d))

        def twos_complement(value, bits):
            if value & (1 << bits - 1):
                return value - (1 << bits)
            return value

        provola1 = libdestruct.inflate(c_int, 0xdeadb000)
        provola2 = libdestruct.inflate(c_uint, 0xdeadb000 + 0x100)
        provola3 = libdestruct.inflate(c_long, 0xdeadb000 + 0x200)
        provola4 = libdestruct.inflate(c_ulong, 0xdeadb000 + 0x300)

        self.assertEqual(provola1.get(), twos_complement(0xdeadbeef, 32))
        self.assertEqual(provola2.value, (0xdeadbeef * 2) & ((1 << 32) - 1))
        self.assertEqual(provola3.get(), twos_complement(0xdeadbeefdeadbeef, 64))
        self.assertEqual(provola4.get(), (0xdeadbeefdeadbeef * 2) & ((1 << 64) - 1))

        self.assertEqual(int(provola1), provola1.value)

        provola1._set(0x1)
        provola2._set(0x2)
        provola3.value = 0x3
        provola4._set(0x4)

        self.assertEqual(bytes(provola1), b"\x01\x00\x00\x00")
        self.assertEqual(bytes(provola2), b"\x02\x00\x00\x00")
        self.assertEqual(bytes(provola3), b"\x03\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(bytes(provola4), b"\x04\x00\x00\x00\x00\x00\x00\x00")

        d.cont()

        self.assertTrue(bp2.hit_on(d))

        d.kill()

        d.terminate()

    def test_integer_type_freeze(self):
        d = debugger("binaries/basic_test")

        d.run()

        bp1 = d.bp("signpost1")

        bp2 = d.bp("signpost2")

        libdestruct = inflater(d.memory)

        d.cont()

        self.assertTrue(bp1.hit_on(d))

        provola1 = libdestruct.inflate(c_int, 0xdeadb000)
        provola2 = libdestruct.inflate(c_uint, 0xdeadb000 + 0x100)
        provola3 = libdestruct.inflate(c_long, 0xdeadb000 + 0x200)
        provola4 = libdestruct.inflate(c_ulong, 0xdeadb000 + 0x300)

        self.assertEqual(provola1.value, 1)
        self.assertEqual(provola2.value, 2)
        self.assertEqual(provola3.value, 3)
        self.assertEqual(provola4.value, 4)

        provola1.freeze()
        provola2.freeze()
        provola3.freeze()
        provola4.freeze()

        d.cont()

        self.assertTrue(bp2.hit_on(d))

        self.assertEqual(provola1.value, 1)
        self.assertEqual(provola2.value, 2)
        self.assertEqual(provola3.value, 3)
        self.assertEqual(provola4.value, 4)

        self.assertEqual(bytes(provola1), b"\x01\x00\x00\x00")
        self.assertEqual(bytes(provola2), b"\x02\x00\x00\x00")
        self.assertEqual(bytes(provola3), b"\x03\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(bytes(provola4), b"\x04\x00\x00\x00\x00\x00\x00\x00")

        self.assertRaises(ValueError, provola1.set, 0x1)

        d.kill()

        d.terminate()

    def test_integer_type_equality(self):
        d = debugger("binaries/basic_test")

        d.run()

        bp1 = d.bp("signpost1")

        bp2 = d.bp("signpost2")

        libdestruct = inflater(d.memory)

        d.cont()

        self.assertTrue(bp1.hit_on(d))

        provola1 = libdestruct.inflate(c_int, 0xdeadb000)
        provola2 = libdestruct.inflate(c_uint, 0xdeadb000 + 0x100)
        provola3 = libdestruct.inflate(c_long, 0xdeadb000 + 0x200)
        provola4 = libdestruct.inflate(c_ulong, 0xdeadb000 + 0x300)

        self.assertEqual(provola1.value, 1)
        self.assertEqual(provola2.value, 2)
        self.assertEqual(provola3.value, 3)
        self.assertEqual(provola4.value, 4)

        self.assertNotEqual(provola1, provola2)

        provola2.set(0x1)

        self.assertEqual(provola1, provola2)

        provola3.freeze()

        provola1.set(0x3)

        self.assertEqual(provola1, provola3)

        d.kill()

        d.terminate()
