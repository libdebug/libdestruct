#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from libdestruct.backing.resolver import Resolver
from libdestruct.common.inflater import Inflater

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.common.obj import obj


_VALID_ENDIANNESS = ("little", "big")


def inflater(memory: Sequence, endianness: str = "little") -> Inflater:
    """Return a TypeInflater instance."""
    if not isinstance(memory, Sequence):
        raise TypeError(f"memory must be a Sequence, not {type(memory).__name__}")

    if endianness not in _VALID_ENDIANNESS:
        raise ValueError(f"endianness must be 'little' or 'big', not {endianness!r}")

    return Inflater(memory, endianness=endianness)


def inflate(item: type, memory: Sequence, address: int | Resolver, endianness: str = "little") -> obj:
    """Inflate a memory-referencing type.

    Args:
        item: The type to inflate.
        memory: The memory view, which can be mutable or immutable.
        address: The address of the object in the memory view.
        endianness: The byte order ("little" or "big").

    Returns:
        The inflated object.
    """
    if not isinstance(address, int) and not isinstance(address, Resolver):
        raise TypeError(f"address must be an int or a Resolver, not {type(address).__name__}")

    return inflater(memory, endianness=endianness).inflate(item, address)
