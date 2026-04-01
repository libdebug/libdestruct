#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.common.union.tagged_union_field import TaggedUnionField


def tagged_union(discriminator: str, variants: dict[object, type]) -> TaggedUnionField:
    """Create a tagged union field descriptor.

    Args:
        discriminator: The name of the struct field used to select the active variant.
        variants: A mapping from discriminator values to variant types.

    Returns:
        A TaggedUnionField for use as a struct field default value.
    """
    return TaggedUnionField(discriminator, variants)
