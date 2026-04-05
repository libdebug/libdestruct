#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.array.vla_field import VLAField

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.common.array.array_field import ArrayField
    from libdestruct.common.obj import obj


def vla_of(element_type: type[obj], count_field: str) -> ArrayField:
    """Return a new variable-length array field.

    Args:
        element_type: The type of each element in the array.
        count_field: The name of the struct field that holds the element count.
    """
    return VLAField(element_type, count_field)
