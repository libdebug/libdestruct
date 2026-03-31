#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from libdestruct.common.field import Field
from libdestruct.common.obj import obj

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver

T = TypeVar("T")

class ptr(obj[T]):
    """A pointer to an object in memory."""

    size: int = 8
    """The size of a pointer in bytes."""

    def __init__(self: ptr, resolver: Resolver, wrapper: type | None = None) -> None:
        """Initialize a pointer.

        Args:
            resolver: The backing value resolver.
            wrapper: The object this pointer points to.
        """
        super().__init__(resolver)
        self.wrapper = wrapper

    def get(self: ptr) -> int:
        """Return the value of the pointer."""
        value = self.resolver.resolve(self.size, 0)
        return int.from_bytes(value, self.endianness)

    def to_bytes(self: obj) -> bytes:
        """Return the serialized representation of the object."""
        if self._frozen:
            return self._frozen_value.to_bytes(self.size, self.endianness)

        return self.resolver.resolve(self.size, 0)

    def _set(self: ptr, value: int) -> None:
        """Set the value of the pointer to the given value."""
        self.resolver.modify(self.size, 0, value.to_bytes(self.size, self.endianness))

    def unwrap(self: ptr, length: int | None = None) -> obj:
        """Return the object pointed to by the pointer.

        Args:
            length: The length of the object in memory this points to.
        """
        address = self.get()

        if self.wrapper:
            if length:
                raise ValueError("Length is not supported when unwrapping a pointer to a wrapper object.")

            return self.wrapper(self.resolver.absolute_from_own(address))

        if not length:
            length = 1

        return self.resolver.resolve(length, 0)

    def try_unwrap(self: ptr, length: int | None = None) -> obj | None:
        """Return the object pointed to by the pointer, if it is valid.

        Args:
            length: The length of the object in memory this points to.
        """
        address = self.get()

        try:
            # If the address is invalid, this will raise an IndexError or ValueError.
            self.resolver.absolute_from_own(address).resolve(length or 1, 0)
        except (IndexError, ValueError):
            return None

        return self.unwrap(length)

    def to_str(self: ptr, _: int = 0) -> str:
        """Return a string representation of the pointer."""
        if not self.wrapper:
            return f"ptr@0x{self.get():x}"

        # Pretty print inflaters:
        if callable(self.wrapper) and hasattr(self.wrapper, "__self__") and isinstance(self.wrapper.__self__, Field):
            name = self.wrapper.__self__.__class__.__qualname__
        else:
            name = self.wrapper.__name__

        return f"{name}@0x{self.get():x}"

    def __str__(self: ptr) -> str:
        """Return a string representation of the pointer."""
        return self.to_str()
