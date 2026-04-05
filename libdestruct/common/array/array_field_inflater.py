#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#


from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.array.array import array
from libdestruct.common.array.linear_array_field import LinearArrayField
from libdestruct.common.array.vla_field import VLAField
from libdestruct.common.array.vla_field_inflater import vla_field_inflater
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


registry = TypeRegistry()


def linear_array_field_inflater(
    field: LinearArrayField,
    _: type[obj],
    __: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Returns the inflater for an array field of a struct."""
    field.item = registry.inflater_for(field.item)

    return field.inflate


def _subscripted_array_handler(
    item: object,
    args: tuple,
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj] | None:
    """Handle subscripted array types like array[c_int, 3] or array[c_int, 'length']."""
    if len(args) != 2:
        return None
    element_type, count = args
    if isinstance(count, str):
        # Variable-length array: count is a field name
        field = VLAField(element_type, count)
        return vla_field_inflater(field, type(None), owner)
    if not isinstance(count, int) or count <= 0:
        raise ValueError(f"array count must be a positive integer, got {count}")
    field = LinearArrayField(element_type, count)
    field.item = registry.inflater_for(element_type)
    return field.inflate


registry.register_instance_handler(LinearArrayField, linear_array_field_inflater)
registry.register_generic_handler(array, _subscripted_array_handler)
