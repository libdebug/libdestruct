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


class UnionField(Field):
    """A field descriptor for a plain (non-discriminated) union in a struct."""

    base_type: type[obj] = union

    def __init__(self: UnionField, variants: dict[str, type]) -> None:
        """Initialize the union field.

        Args:
            variants: A mapping from variant names to their types.
        """
        self.variants = variants

    def inflate(self: UnionField, resolver: Resolver | None) -> union:
        """Inflate the field (used during size computation with resolver=None).

        Args:
            resolver: The backing resolver (None during size computation).
        """
        return union(resolver, None, self.get_size())

    def get_size(self: UnionField) -> int:
        """Return the size of the union (max of all variant sizes)."""
        return max(size_of(variant) for variant in self.variants.values())

    def get_alignment(self: UnionField) -> int:
        """Return the alignment of the union (max of all variant alignments)."""
        return max(alignment_of(variant) for variant in self.variants.values())
