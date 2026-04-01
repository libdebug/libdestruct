#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.c.c_integer_types import c_int
from libdestruct.common.enum.enum import enum
from libdestruct.common.enum.int_enum_field import IntEnumField
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.enum.enum_field import EnumField
    from libdestruct.common.obj import obj

registry = TypeRegistry()


def generic_enum_field_inflater(
    field: EnumField,
    _: type[obj],
    __: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Returns the inflater for an enum field of a struct."""
    return field.inflate


def _subscripted_enum_handler(
    item: object,
    args: tuple,
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj] | None:
    """Handle subscripted enum types like enum[MyEnum] or enum[MyEnum, c_short]."""
    if not args:
        return None
    python_enum = args[0]
    backing_type = args[1] if len(args) > 1 else c_int
    field = IntEnumField(python_enum, size=backing_type.size)
    return field.inflate


registry.register_instance_handler(IntEnumField, generic_enum_field_inflater)
registry.register_generic_handler(enum, _subscripted_enum_handler)
