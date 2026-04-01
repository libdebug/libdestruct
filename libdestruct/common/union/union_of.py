#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.common.union.union_field import UnionField


def union_of(variants: dict[str, type]) -> UnionField:
    """Create a plain union field descriptor.

    Args:
        variants: A mapping from variant names to their types.

    Returns:
        A UnionField for use as a struct field default value.
    """
    return UnionField(variants)
