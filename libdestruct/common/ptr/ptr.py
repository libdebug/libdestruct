#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TypeVar

from libdestruct.backing.resolver import Resolver
from libdestruct.common.field import Field
from libdestruct.common.obj import obj
from libdestruct.common.utils import size_of

T = TypeVar("T")


class _ArithmeticResolver(Resolver):
    """A resolver for pointers produced by arithmetic operations.

    Stores a fixed address but delegates memory access to the original resolver.
    """

    def __init__(self: _ArithmeticResolver, original: Resolver, address: int) -> None:
        self._original = original
        self._address = address
        self.endianness = original.endianness

    def resolve_address(self: _ArithmeticResolver) -> int:
        return self._address

    def resolve(self: _ArithmeticResolver, size: int, _: int) -> bytes:
        return self._address.to_bytes(size, self.endianness)

    def modify(self: _ArithmeticResolver, _size: int, _index: int, _value: bytes) -> None:
        raise RuntimeError("Cannot modify a synthetic pointer.")

    def absolute_from_own(self: _ArithmeticResolver, address: int) -> Resolver:
        return self._original.absolute_from_own(address)

    def relative_from_own(self: _ArithmeticResolver, address_offset: int, _index_offset: int) -> Resolver:
        return self._original.absolute_from_own(self._address + address_offset)


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
        self._cached_unwrap: obj | None = None
        self._cache_valid: bool = False

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
        self.invalidate()

    def invalidate(self: ptr) -> None:
        """Clear the cached unwrap result."""
        self._cached_unwrap = None
        self._cache_valid = False

    def unwrap(self: ptr, length: int | None = None) -> obj:
        """Return the object pointed to by the pointer.

        Args:
            length: The length of the object in memory this points to.
        """
        if self._cache_valid:
            return self._cached_unwrap

        address = self.get()

        if self.wrapper:
            if length:
                raise ValueError("Length is not supported when unwrapping a pointer to a wrapper object.")

            result = self.wrapper(self.resolver.absolute_from_own(address))
        else:
            target_resolver = self.resolver.absolute_from_own(address)
            result = target_resolver.resolve(length or 1, 0)

        self._cached_unwrap = result
        self._cache_valid = True
        return result

    def try_unwrap(self: ptr, length: int | None = None) -> obj | None:
        """Return the object pointed to by the pointer, if it is valid.

        Args:
            length: The length of the object in memory this points to.
        """
        if self._cache_valid:
            return self._cached_unwrap

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

    @property
    def _element_size(self: ptr) -> int:
        """Return the byte size of the pointed-to element."""
        if self.wrapper is None:
            return 1
        return size_of(self.wrapper)

    def __add__(self: ptr, n: int) -> ptr:
        """Return a new pointer advanced by n elements."""
        new_addr = self.get() + n * self._element_size
        return ptr(_ArithmeticResolver(self.resolver, new_addr), self.wrapper)

    def __sub__(self: ptr, n: int) -> ptr:
        """Return a new pointer retreated by n elements."""
        new_addr = self.get() - n * self._element_size
        return ptr(_ArithmeticResolver(self.resolver, new_addr), self.wrapper)

    def __getitem__(self: ptr, n: int) -> obj:
        """Return the object at index n relative to this pointer."""
        return (self + n).unwrap()

    def __str__(self: ptr) -> str:
        """Return a string representation of the pointer."""
        return self.to_str()
