#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.backing.resolver import Resolver

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import MutableSequence


class MemoryResolver(Resolver):
    """A class that can resolve itself to a value in a referenced memory storage."""

    def __init__(self: MemoryResolver, memory: MutableSequence, address: int | None, endianness: str = "little") -> None:
        """Initializes a basic memory resolver."""
        self.memory = memory
        self.address = address
        self.parent = None
        self.offset = None
        self.endianness = endianness

    def resolve_address(self: MemoryResolver) -> int:
        """Resolves self's address, mainly used by childs to determine their own address."""
        if self.address is not None:
            return self.address

        return self.parent.resolve_address() + self.offset

    def relative_from_own(self: MemoryResolver, address_offset: int, _: int) -> MemoryResolver:
        """Creates a resolver that references a parent, such that a change in the parent is propagated on the child."""
        new_resolver = MemoryResolver(self.memory, None, self.endianness)
        new_resolver.parent = self
        new_resolver.offset = address_offset
        return new_resolver

    def absolute_from_own(self: MemoryResolver, address: int) -> MemoryResolver:
        """Creates a resolver that has an absolute reference to an object, from the parent's view."""
        return MemoryResolver(self.memory, address, self.endianness)

    def resolve(self: MemoryResolver, size: int, _: int) -> bytes:
        """Resolves itself, providing the bytes it references for the specified size and index."""
        address = self.resolve_address()
        return bytes(self.memory[address : address + size])

    def modify(self: MemoryResolver, size: int, _: int, value: bytes) -> None:
        """Modifies itself in memory."""
        address = self.resolve_address()
        self.memory[address : address + size] = value
