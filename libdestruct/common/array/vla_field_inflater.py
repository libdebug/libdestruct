#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.array.vla_field import VLAField
from libdestruct.common.array.vla_impl import vla_impl
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj

registry = TypeRegistry()


def vla_field_inflater(
    field: VLAField,
    _: type[obj],
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Return the inflater for a variable-length array field.

    During size computation (owner[0] is None), returns field.inflate which
    is a bound method on a Field — ``size_of`` detects this and calls
    ``get_size()`` (returns 0) without ever invoking the method.

    During actual inflation, returns a closure that creates a ``vla_impl``
    holding a reference to the count member for dynamic count reads.
    """
    if owner is None or owner[0] is None:
        field.item = registry.inflater_for(field.item)
        return field.inflate

    struct_instance = owner[0]
    element_inflater = registry.inflater_for(field.item)

    def inflate_vla(resolver: Resolver) -> vla_impl:
        members = object.__getattribute__(struct_instance, "_members")
        count_member = members[field.count_field]
        return vla_impl(resolver, element_inflater, count_member)

    return inflate_vla


registry.register_instance_handler(VLAField, vla_field_inflater)
