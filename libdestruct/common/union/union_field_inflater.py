#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.type_registry import TypeRegistry
from libdestruct.common.union.union import union
from libdestruct.common.union.union_field import UnionField

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj

registry = TypeRegistry()


def union_field_inflater(
    field: UnionField,
    _: type[obj],
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Return the inflater for a plain union field.

    During size computation (owner[0] is None), returns field.inflate which
    creates a stub with the correct max size.

    During actual inflation, returns a closure that inflates all variants
    at the same memory location.
    """
    if owner is None or owner[0] is None:
        return field.inflate

    def inflate_all_variants(resolver: Resolver) -> union:
        variants = {}
        for name, variant_type in field.variants.items():
            variant_inflater = registry.inflater_for(variant_type)
            variants[name] = variant_inflater(resolver)

        return union(resolver, None, field.get_size(), variants=variants)

    return inflate_all_variants


registry.register_instance_handler(UnionField, union_field_inflater)
