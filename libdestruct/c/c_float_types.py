#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import struct

from libdestruct.common.obj import obj


class _c_float_base(obj):
    """A generic C floating-point type, to be subclassed by c_float and c_double."""

    size: int
    """The size of the float in bytes."""

    _format: str
    """The struct format character ('f' or 'd')."""

    _frozen_value: float | None = None
    """The frozen value of the float."""

    def _format_char(self: _c_float_base) -> str:
        prefix = "<" if self.endianness == "little" else ">"
        return prefix + self._format

    def get(self: _c_float_base) -> float:
        """Return the value of the float."""
        return struct.unpack(self._format_char(), self.resolver.resolve(self.size, 0))[0]

    def _set(self: _c_float_base, value: float) -> None:
        """Set the value of the float."""
        self.resolver.modify(self.size, 0, struct.pack(self._format_char(), value))

    def to_bytes(self: _c_float_base) -> bytes:
        """Return the serialized representation of the float."""
        if self._frozen:
            return struct.pack(self._format_char(), self._frozen_value)
        return self.resolver.resolve(self.size, 0)

    def __float__(self: _c_float_base) -> float:
        """Return the value as a Python float."""
        return self.get()

    def __int__(self: _c_float_base) -> int:
        """Return the value as a Python int."""
        return int(self.get())


class c_float(_c_float_base):
    """A C float (IEEE 754 single-precision, 32-bit)."""

    size: int = 4
    _format: str = "f"


class c_double(_c_float_base):
    """A C double (IEEE 754 double-precision, 64-bit)."""

    size: int = 8
    _format: str = "d"
