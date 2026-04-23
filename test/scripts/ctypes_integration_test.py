#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

try:
    from ctypes import c_time_t
except ImportError:
    from ctypes import c_long as c_time_t

from ctypes import *
from libdebug import debugger
from libdestruct import inflater, struct

class CtypesTest(unittest.TestCase):
    def test_all_types(self):
        d = debugger("binaries/ctypes_test")

        d.run()

        bp = d.breakpoint("leak")
        check = d.breakpoint("correct")

        class provola(struct):
            a: c_bool
            b: c_ushort
            c: c_char
            d: c_char_p
            e: c_double
            f: c_float
            g: c_int
            h: c_int16
            i: c_int32
            j: c_int64
            k: c_int8
            l: c_long
            m: c_longdouble
            n: c_longlong
            o: c_short
            p: c_size_t
            r: c_time_t
            s: c_void_p
            t: c_uint
            u: c_uint16
            v: c_uint32
            w: c_uint64
            x: c_uint8
            y: c_ulong
            z: c_ulonglong

        libdestruct = inflater(d.memory)

        d.cont()

        self.assertTrue(bp.hit_on(d))

        obj = libdestruct.inflate(provola, d.regs.rdi)

        self.assertEqual(obj.a.value, True)
        self.assertEqual(obj.b.value, 1337)
        self.assertEqual(obj.c.value, b'\x17')
        self.assertAlmostEqual(obj.e.value, 1337.1337)
        self.assertAlmostEqual(obj.f.value, 123.456, places=5)
        self.assertEqual(obj.g.value, 12345)
        self.assertEqual(obj.h.value, 23456)
        self.assertEqual(obj.i.value, 0x0eadbeef)
        self.assertEqual(obj.j.value, 0x0eadbeefdeadbeef)
        self.assertEqual(obj.k.value, 123)
        self.assertEqual(obj.l.value, 0xeefd00dbeefd00d)
        self.assertAlmostEqual(obj.m.value, 123456.789)
        self.assertEqual(obj.n.value, 0xeefdeadbeefdead)
        self.assertEqual(obj.o.value, 9876)
        self.assertEqual(obj.p.value, 0xdeadbeefdeadbeef)
        self.assertEqual(obj.r.value, 0x123456)
        self.assertEqual(obj.s.value, 0x1234)
        self.assertEqual(obj.t.value, 0xdeadbeef)
        self.assertEqual(obj.u.value, 0x1234)
        self.assertEqual(obj.v.value, 0xd00dbeef)
        self.assertEqual(obj.w.value, 0xd00ddeadbeefbeef)
        self.assertEqual(obj.x.value, 0x46)
        self.assertEqual(obj.y.value, 0xbeefbeefbeef)
        self.assertEqual(obj.z.value, 0xd00dd00dd00dd00d)

        obj.a.value = False
        obj.b.value = 1234
        obj.c.value = b'\x23'
        obj.e.value = 1234.5678
        obj.f.value = 234.567
        obj.g.value = 23456
        obj.h.value = 32767
        obj.i.value = 0xadbeef
        obj.j.value = 0xadbeefdeadbeef
        obj.k.value = 98
        obj.l.value = 0xadbeefd00dbeef
        obj.m.value = 345.678
        obj.n.value = 0xedbeefdeadbeef
        obj.o.value = 8765
        obj.p.value = 0xeadbeefdeadbeef
        obj.r.value = 0x234567
        obj.s.value = 0x2345
        obj.t.value = 0xeadbeef
        obj.u.value = 0x2345
        obj.v.value = 0xbadbeef
        obj.w.value = 0xbadbeefbadbeef
        obj.x.value = 0x28
        obj.y.value = 0xbadbadbadbad
        obj.z.value = 0xbadd00dbadd00d

        d.cont()

        self.assertTrue(check.hit_on(d))

        d.kill()
        d.terminate()