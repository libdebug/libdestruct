#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

try:  # pragma: no cover
    from rich.traceback import install

    install()
except ImportError:  # pragma: no cover
    pass

from libdestruct.backing.resolver import Resolver
from libdestruct.c import c_char, c_double, c_float, c_int, c_long, c_short, c_str, c_uchar, c_uint, c_ulong, c_ushort
from libdestruct.common.array import array, array_of
from libdestruct.common.attributes import offset
from libdestruct.common.bitfield import bitfield_of
from libdestruct.common.enum import enum, enum_of
from libdestruct.common.ptr.ptr import ptr
from libdestruct.common.struct import ptr_to, ptr_to_self, struct
from libdestruct.common.union import tagged_union, union, union_of
from libdestruct.common.utils import size_of
from libdestruct.libdestruct import inflate, inflater

__all__ = [
    "Resolver",
    "array",
    "array_of",
    "bitfield_of",
    "c_char",
    "c_double",
    "c_float",
    "c_int",
    "c_long",
    "c_short",
    "c_str",
    "c_uchar",
    "c_uint",
    "c_ulong",
    "c_ushort",
    "enum",
    "enum_of",
    "inflate",
    "inflater",
    "offset",
    "ptr",
    "ptr_to",
    "ptr_to_self",
    "size_of",
    "struct",
    "tagged_union",
    "union",
    "union_of",
]
