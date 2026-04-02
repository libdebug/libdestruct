#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.array.array_field import ArrayField

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


class VLAField(ArrayField):
    """A generator for a variable-length array whose count is determined by another struct field.

    At size-computation time, ``vla_field_inflater`` returns ``field.inflate``
    as a bound method so that ``size_of`` can call ``get_size()`` (returns 0).
    ``inflate`` itself is never invoked; the real inflation is handled by the
    closure built in ``vla_field_inflater`` which reads the count at runtime.
    """

    def __init__(self: VLAField, element_type: type[obj], count_field: str) -> None:
        """Initialize the field."""
        self.item = element_type
        self.count_field = count_field

    def inflate(self: VLAField, resolver: Resolver) -> None:
        """Placeholder — never called at runtime.

        ``size_of`` detects the bound method via ``is_field_bound_method`` and
        calls ``get_size()`` directly, so this body is unreachable.
        """
        raise NotImplementedError("VLAField.inflate is a size-computation stub; use vla_field_inflater instead")

    def get_size(self: VLAField) -> int:
        """VLA has zero static size — actual size is determined at inflation time."""
        return 0
