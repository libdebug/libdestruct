#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.field import Field
from libdestruct.common.union.union import union
from libdestruct.common.utils import alignment_of, size_of

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


class TaggedUnionField(Field):
    """A field descriptor for a tagged union in a struct."""

    base_type: type[obj] = union

    def __init__(self: TaggedUnionField, discriminator: str, variants: dict[object, type]) -> None:
        """Initialize the tagged union field.

        Args:
            discriminator: The name of the struct field used as the discriminator.
            variants: A mapping from discriminator values to variant types.
        """
        self.discriminator = discriminator
        self.variants = variants

    def inflate(self: TaggedUnionField, resolver: Resolver | None) -> union:
        """Inflate the field (used during size computation with resolver=None).

        Args:
            resolver: The backing resolver (None during size computation).
        """
        return union(resolver, None, self.get_size())

    def get_size(self: TaggedUnionField) -> int:
        """Return the size of the union (max of all variant sizes)."""
        return max(size_of(variant) for variant in self.variants.values())

    def get_alignment(self: TaggedUnionField) -> int:
        """Return the alignment of the union (max of all variant alignments)."""
        return max(alignment_of(variant) for variant in self.variants.values())
