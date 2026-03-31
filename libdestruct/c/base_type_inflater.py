#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.c.c_float_types import c_double, c_float
from libdestruct.c.c_integer_types import _c_integer, c_char, c_int, c_long, c_short, c_uchar, c_uint, c_ulong, c_ushort
from libdestruct.c.c_str import c_str
from libdestruct.common.type_registry import TypeRegistry

registry = TypeRegistry()


registry.register_mapping(_c_integer, _c_integer)
registry.register_mapping(c_char, c_char)
registry.register_mapping(c_uchar, c_uchar)
registry.register_mapping(c_short, c_short)
registry.register_mapping(c_ushort, c_ushort)
registry.register_mapping(c_int, c_int)
registry.register_mapping(c_uint, c_uint)
registry.register_mapping(c_long, c_long)
registry.register_mapping(c_ulong, c_ulong)
registry.register_mapping(c_float, c_float)
registry.register_mapping(c_double, c_double)
registry.register_mapping(c_str, c_str)
