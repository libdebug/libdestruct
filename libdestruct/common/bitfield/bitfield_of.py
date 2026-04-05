#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.bitfield.bitfield_field import BitfieldField

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.common.obj import obj


def bitfield_of(backing_type: type[obj], bit_width: int) -> BitfieldField:
    """Create a bitfield descriptor for use in struct annotations.

    Args:
        backing_type: The backing integer type (e.g., c_int, c_uint).
        bit_width: The number of bits this field occupies.
    """
    if bit_width <= 0:
        raise ValueError("Bit width must be positive.")

    if hasattr(backing_type, "size") and bit_width > backing_type.size * 8:
        raise ValueError(f"Bit width {bit_width} exceeds backing type size ({backing_type.size * 8} bits).")

    return BitfieldField(backing_type, bit_width)
