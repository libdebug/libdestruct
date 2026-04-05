#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.c.c_integer_types import c_int
from libdestruct.common.flags.flags import flags
from libdestruct.common.flags.int_flag_field import IntFlagField
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.flags.flags_field import FlagsField
    from libdestruct.common.obj import obj

registry = TypeRegistry()


def generic_flags_field_inflater(
    field: FlagsField,
    _: type[obj],
    __: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Returns the inflater for a flags field of a struct."""
    return field.inflate


def _subscripted_flags_handler(
    item: object,
    args: tuple,
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj] | None:
    """Handle subscripted flags types like flags[Perms] or flags[Perms, c_short]."""
    if not args:
        return None
    python_flag = args[0]
    backing_type = args[1] if len(args) > 1 else c_int
    field = IntFlagField(python_flag, backing_type=backing_type)
    return field.inflate


registry.register_instance_handler(IntFlagField, generic_flags_field_inflater)
registry.register_generic_handler(flags, _subscripted_flags_handler)
