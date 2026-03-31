#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.obj import obj
from libdestruct.common.type_registry import TypeRegistry
from libdestruct.libdestruct import inflater

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.common.struct.struct_impl import struct_impl


class struct(obj):
    """A C struct."""

    def __init__(self: struct) -> None:
        """Initialize the struct."""
        raise RuntimeError("This type should not be directly instantiated.")

    def __new__(cls: type[struct], *args: ..., **kwargs: ...) -> struct:  # noqa: PYI034
        """Create a new struct."""
        # Look for an inflater for this struct
        type_impl = TypeRegistry().inflater_for(cls)
        return type_impl(*args, **kwargs)

    @classmethod
    def from_bytes(cls: type[struct], data: bytes) -> struct_impl:
        """Create a struct from a serialized representation."""
        type_inflater = inflater(data)

        return type_inflater.inflate(cls, 0)
