#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from libdestruct.common.field import Field
from libdestruct.common.flags.flags import flags

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


class FlagsField(Field):
    """A generator for a flags field."""

    base_type: type[obj] = flags

    @abstractmethod
    def inflate(self: FlagsField, resolver: Resolver) -> flags:
        """Inflate the field."""
