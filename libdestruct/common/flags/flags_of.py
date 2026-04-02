#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from enum import IntFlag
from typing import TYPE_CHECKING

from libdestruct.common.flags.int_flag_field import IntFlagField

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.common.flags.flags_field import FlagsField


def flags_of(flag_type: type[IntFlag], lenient: bool = True, size: int = 4) -> FlagsField:
    """Return a new flags field."""
    if not issubclass(flag_type, IntFlag):
        raise TypeError("The flag type must be a subclass of IntFlag.")

    return IntFlagField(flag_type, lenient, size)
