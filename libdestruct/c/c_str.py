#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.common.array.array import array


class c_str(array):
    """A C string."""

    def count(self: c_str) -> int:
        """Return the size of the string."""
        size = 0

        try:
            while self.resolver.resolve(size, 0)[-1:] != b"\x00":
                size += 1
        except IndexError as e:
            raise RuntimeError("String is not null-terminated.") from e

        return size - 1

    def get(self: c_str, index: int = -1) -> bytes:
        """Return the character at the given index."""
        if (index != -1 and index < 0) or index >= self.count():
            raise IndexError("String index out of range.")

        if index == -1:
            return self.resolver.resolve(self.count(), 0)

        return bytes([self.resolver.resolve(index + 1, 0)[-1]])

    def to_bytes(self: c_str) -> bytes:
        """Return the serialized representation of the object."""
        return self.resolver.resolve(self.count(), 0)

    def _set(self: c_str, value: bytes, index: int = -1) -> None:
        """Set the character at the given index to the given value."""
        if (index != -1 and index < 0) or index >= self.count():
            raise IndexError("String index out of range.")

        if index == -1:
            # This is rather clunky
            self.resolver.modify(len(value), 0, value)
        else:
            prev = self.resolver.resolve(index, 0)
            self.resolver.modify(index + len(value), 0, prev + value)

    def __setitem__(self: c_str, index: int, value: bytes) -> None:
        """Set the character at the given index to the given value."""
        self._set(value, index)

    def __iter__(self: c_str) -> iter:
        """Return an iterator over the string."""
        for i in range(self.count()):
            yield self.get(i)
