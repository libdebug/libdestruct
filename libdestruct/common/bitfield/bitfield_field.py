#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.field import Field

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


class BitfieldField(Field):
    """A generator for a bitfield within a struct."""

    base_type: type[obj]

    def __init__(self: BitfieldField, backing_type: type, bit_width: int) -> None:
        """Initialize the bitfield field.

        Args:
            backing_type: The backing integer type (e.g., c_int, c_uint).
            bit_width: The number of bits this field occupies.
        """
        self.backing_type = backing_type
        self.bit_width = bit_width
        self.base_type = backing_type

    def inflate(self: BitfieldField, resolver: Resolver) -> obj:
        """Inflate the field. Not used directly — struct_impl handles bitfield inflation."""
        raise NotImplementedError("BitfieldField inflation is handled by struct_impl.")

    def get_size(self: BitfieldField) -> int:
        """Returns 0 — bitfields do not independently advance the struct offset."""
        return 0
