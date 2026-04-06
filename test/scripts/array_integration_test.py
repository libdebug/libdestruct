#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdebug import debugger
from libdestruct import array, array_of, inflater, c_int, c_long, struct

class ArrayTest(unittest.TestCase):
    def test_linear_arrays_1(self):
        d = debugger("binaries/array_test")

        d.run()

        bp = d.bp("do_nothing")

        d.cont()

        libdestruct = inflater(d.memory)

        self.assertTrue(bp.hit_on(d))

        test1 = libdestruct.inflate(array_of(c_int, 10), d.regs.rdi)

        self.assertEqual(len(test1), 10)

        for i in range(10):
            self.assertEqual(test1[i].value, i ** 2)

        self.assertEqual(bytes(test1), b"".join((i ** 2).to_bytes(4, "little") for i in range(10)))

        self.assertIn(test1[0], test1)

        d.cont()

        class test2_t(struct):
            a: c_int

        test2 = libdestruct.inflate(array_of(test2_t, 10), d.regs.rdi)

        for i in range(10):
            self.assertEqual(test2[i].a.value, i ** 3)

        d.cont()

        class test3_t(struct):
            a: c_int
            b: c_long

        test3 = libdestruct.inflate(array_of(test3_t, 10), d.regs.rdi)

        for i in range(10):
            self.assertEqual(test3[i].a.value, i * 100)
            self.assertEqual(test3[i].b.value, i * 1000)

        d.cont()

        class test4_t(struct):
            a: c_int
            b: array = array_of(c_int, 10)

        test4 = libdestruct.inflate(array_of(test4_t, 10), d.regs.rdi)

        for i in range(10):
            self.assertEqual(test4[i].a.value, i ** 4)
            for j in range(10):
                self.assertEqual(test4[i].b[j].value, (i + 1) * j)

        with self.assertRaises(NotImplementedError):
            test4[i] = 4

        with self.assertRaises(NotImplementedError):
            test4._set([1, 2, 3])

        with self.assertRaises(NotImplementedError):
            test4.set([1, 2, 3])

        d.kill()
        d.terminate()
