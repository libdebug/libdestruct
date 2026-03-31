#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import struct

from libdestruct.common.obj import obj


class c_float(obj):
    """A C float (IEEE 754 single-precision, 32-bit)."""

    size: int = 4
    """The size of a float in bytes."""

    _frozen_value: float | None = None
    """The frozen value of the float."""

    def _format_char(self: c_float) -> str:
        return "<f" if self.endianness == "little" else ">f"

    def get(self: c_float) -> float:
        """Return the value of the float."""
        return struct.unpack(self._format_char(), self.resolver.resolve(self.size, 0))[0]

    def _set(self: c_float, value: float) -> None:
        """Set the value of the float."""
        self.resolver.modify(self.size, 0, struct.pack(self._format_char(), value))

    def to_bytes(self: c_float) -> bytes:
        """Return the serialized representation of the float."""
        if self._frozen:
            return struct.pack(self._format_char(), self._frozen_value)
        return self.resolver.resolve(self.size, 0)

    def __float__(self: c_float) -> float:
        """Return the value as a Python float."""
        return self.get()


class c_double(obj):
    """A C double (IEEE 754 double-precision, 64-bit)."""

    size: int = 8
    """The size of a double in bytes."""

    _frozen_value: float | None = None
    """The frozen value of the double."""

    def _format_char(self: c_double) -> str:
        return "<d" if self.endianness == "little" else ">d"

    def get(self: c_double) -> float:
        """Return the value of the double."""
        return struct.unpack(self._format_char(), self.resolver.resolve(self.size, 0))[0]

    def _set(self: c_double, value: float) -> None:
        """Set the value of the double."""
        self.resolver.modify(self.size, 0, struct.pack(self._format_char(), value))

    def to_bytes(self: c_double) -> bytes:
        """Return the serialized representation of the double."""
        if self._frozen:
            return struct.pack(self._format_char(), self._frozen_value)
        return self.resolver.resolve(self.size, 0)

    def __float__(self: c_double) -> float:
        """Return the value as a Python float."""
        return self.get()
