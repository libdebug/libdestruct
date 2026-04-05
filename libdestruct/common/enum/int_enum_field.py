#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.c.c_integer_types import c_char, c_int, c_long, c_short
from libdestruct.common.enum.enum import enum
from libdestruct.common.enum.enum_field import EnumField

if TYPE_CHECKING:  # pragma: no cover
    from enum import IntEnum

    from libdestruct.backing.resolver import Resolver


class IntEnumField(EnumField):
    """A generator for an enum of integers."""

    def __init__(
        self: IntEnumField,
        enum: type[IntEnum],
        lenient: bool = True,
        size: int = 4,
        backing_type: type | None = None,
    ) -> None:
        """Initialize the field.

        Args:
            enum: The enum class.
            lenient: Whether the conversion is lenient or not.
            size: The size of the field in bytes (used when backing_type is not provided).
            backing_type: The explicit backing type to use. If provided, overrides size.
        """
        self.enum = enum
        self.lenient = lenient

        if backing_type is not None:
            self.backing_type = backing_type
            return

        if not 0 < size <= 8:
            raise ValueError("The size of the field must be between 1 and 8 bytes.")

        match size:
            case 1:
                self.backing_type = c_char
            case 2:
                self.backing_type = c_short
            case 4:
                self.backing_type = c_int
            case 8:
                self.backing_type = c_long
            case _:
                raise ValueError("The size of the field must be a power of 2.")

    def inflate(self: IntEnumField, resolver: Resolver) -> int:
        """Inflate the field.

        Args:
            resolver: The backing resolver for the object.
        """
        return enum(resolver, self.enum, self.backing_type, self.lenient)

    def get_size(self: IntEnumField) -> int:
        """Returns the size of the object inflated by this field."""
        return self.backing_type.size
