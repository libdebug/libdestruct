#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.type_registry import TypeRegistry
from libdestruct.common.union.tagged_union_field import TaggedUnionField
from libdestruct.common.union.union import union

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj

registry = TypeRegistry()


def tagged_union_field_inflater(
    field: TaggedUnionField,
    _: type[obj],
    owner: tuple[obj, type[obj]] | None,
) -> Callable[[Resolver], obj]:
    """Return the inflater for a tagged union field.

    During size computation (owner[0] is None), returns field.inflate which
    creates a stub with the correct max size.

    During actual inflation, returns a closure that reads the discriminator
    from the struct instance and inflates the matching variant.
    """
    if owner is None or owner[0] is None:
        return field.inflate

    struct_instance = owner[0]

    def inflate_with_discriminator(resolver: Resolver) -> union:
        members = object.__getattribute__(struct_instance, "_members")
        disc_value = members[field.discriminator].value

        if disc_value not in field.variants:
            raise ValueError(
                f"Unknown discriminator value {disc_value!r} for field '{field.discriminator}'. "
                f"Valid values: {list(field.variants.keys())}"
            )

        variant_type = field.variants[disc_value]
        variant_inflater = registry.inflater_for(variant_type)
        variant = variant_inflater(resolver)

        return union(resolver, variant, field.get_size())

    return inflate_with_discriminator


registry.register_instance_handler(TaggedUnionField, tagged_union_field_inflater)
