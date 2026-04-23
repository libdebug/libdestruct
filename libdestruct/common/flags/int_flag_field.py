#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.c.c_integer_types import signed_integer_for_size
from libdestruct.common.flags.flags import flags
from libdestruct.common.flags.flags_field import FlagsField

if TYPE_CHECKING:  # pragma: no cover
    from enum import IntFlag

    from libdestruct.backing.resolver import Resolver


class IntFlagField(FlagsField):
    """A generator for an IntFlag-based flags field."""

    def __init__(
        self: IntFlagField,
        flag_type: type[IntFlag],
        lenient: bool = True,
        size: int = 4,
        backing_type: type | None = None,
    ) -> None:
        """Initialize the field."""
        self.flag_type = flag_type
        self.lenient = lenient

        if backing_type is not None:
            self.backing_type = backing_type
            return

        self.backing_type = signed_integer_for_size(size)

    def inflate(self: IntFlagField, resolver: Resolver) -> flags:
        """Inflate the field."""
        return flags(resolver, self.flag_type, self.backing_type, self.lenient)

    def get_size(self: IntFlagField) -> int:
        """Returns the size of the object inflated by this field."""
        return self.backing_type.size
