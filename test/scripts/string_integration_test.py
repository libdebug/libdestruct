#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdebug import debugger
from libdestruct import inflater, c_str

class StringTest(unittest.TestCase):
    def test_basic(self):
        d = debugger("binaries/string_test")

        def callback(_, __):
            pass

        d.run()

        bp1 = d.bp("signpost1")
        bp2 = d.bp("signpost2")
        check = d.bp("check", callback=callback)

        d.cont()

        self.assertTrue(bp1.hit_on(d))

        libdestruct = inflater(d.memory)

        string = libdestruct.inflate(c_str, d.regs.rdi)

        self.assertEqual(string.value, b"Hello, world!")

        string.value = b"Hello, WORLD!"

        d.cont()

        self.assertTrue(bp2.hit_on(d))

        self.assertEqual(string.value, b"Hello,")

        string.value = b", world!\x00"

        d.cont()

        d.kill()

        self.assertEqual(check.hit_count, 0)

        d.terminate()
