#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.common.obj import obj


class _c_integer(obj):
    """A generic C integer, to be subclassed by signed and unsigned integers."""

    size: int
    """The size of an integer in bytes."""

    signed: bool
    """Whether the integer is signed."""

    _frozen_value: int | None = None
    """The frozen value of the integer."""

    def get(self: _c_integer) -> int:
        """Return the value of the integer."""
        return int.from_bytes(self.resolver.resolve(self.size, 0), self.endianness, signed=self.signed)

    def to_bytes(self: _c_integer) -> bytes:
        """Return the serialized representation of the object."""
        if self._frozen:
            return self._frozen_value.to_bytes(self.size, self.endianness, signed=self.signed)

        return self.resolver.resolve(self.size, 0)

    def _set(self: _c_integer, value: int) -> None:
        """Set the value of the integer to the given value."""
        self.resolver.modify(
            self.size,
            0,
            value.to_bytes(
                self.size,
                self.endianness,
                signed=self.signed,
            ),
        )

    def __int__(self: _c_integer) -> int:
        """Return the value of the integer."""
        return self.get()


class c_char(_c_integer):
    """A C char."""

    size: int = 1
    """The size of a char in bytes."""

    signed: bool = True
    """Whether the char is signed."""


class c_uchar(_c_integer):
    """A C unsigned char."""

    size: int = 1
    """The size of a char in bytes."""

    signed: bool = False
    """Whether the char is signed."""


class c_short(_c_integer):
    """A C short."""

    size: int = 2
    """The size of a short in bytes."""

    signed: bool = True
    """Whether the short is signed."""


class c_ushort(_c_integer):
    """A C unsigned short."""

    size: int = 2
    """The size of a short in bytes."""

    signed: bool = False
    """Whether the short is signed."""


class c_int(_c_integer):
    """A C integer."""

    size: int = 4
    """The size of an integer in bytes."""

    signed: bool = True
    """Whether the integer is signed."""


class c_uint(_c_integer):
    """A C unsigned integer."""

    size: int = 4
    """The size of an integer in bytes."""

    signed: bool = False
    """Whether the integer is signed."""


class c_long(_c_integer):
    """A C long."""

    size: int = 8
    """The size of a long in bytes."""

    signed: bool = True
    """Whether the long is signed."""


class c_ulong(_c_integer):
    """A C unsigned long."""

    size: int = 8
    """The size of a long in bytes."""

    signed: bool = False
    """Whether the long is signed."""


_SIGNED_INTEGER_BY_SIZE: dict[int, type[_c_integer]] = {
    1: c_char,
    2: c_short,
    4: c_int,
    8: c_long,
}


def signed_integer_for_size(size: int) -> type[_c_integer]:
    """Return the signed C integer type for the given byte size (1, 2, 4, or 8)."""
    if size not in _SIGNED_INTEGER_BY_SIZE:
        raise ValueError("The size of the field must be 1, 2, 4, or 8 bytes.")
    return _SIGNED_INTEGER_BY_SIZE[size]
