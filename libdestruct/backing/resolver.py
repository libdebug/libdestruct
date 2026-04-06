#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from typing_extensions import Self


class Resolver(ABC):
    """A class that can resolve itself to a value, either in memory or in other storage types."""

    parent: Self

    endianness: Literal["little", "big"] = "little"
    """The endianness of the data this resolver accesses."""

    @abstractmethod
    def relative_from_own(self: Resolver, address_offset: int, index_offset: int) -> Self:
        """Creates a resolver that references a parent, such that a change in the parent is propagated on the child."""

    @abstractmethod
    def absolute_from_own(self: Resolver, address: int) -> Self:
        """Creates a resolver that has an absolute reference to an object, from the parent's view."""

    @abstractmethod
    def resolve_address(self: Resolver) -> int:
        """Resolves self's address, mainly used by childs to determine their own address."""

    @abstractmethod
    def resolve(self: Resolver, size: int, index: int) -> bytes:
        """Resolves itself, providing the bytes it references for the specified size and index."""

    @abstractmethod
    def modify(self: Resolver, size: int, index: int, value: bytes) -> None:
        """Modifies itself."""
