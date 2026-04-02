#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.array.array import array
from libdestruct.common.array.array_impl import array_impl
from libdestruct.common.utils import size_of

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


class vla_impl(array_impl):
    """An array whose element count is read dynamically from a sibling struct field."""

    _count_member: obj
    """The struct member whose .value gives the current element count."""

    def __init__(
        self: vla_impl,
        resolver: Resolver,
        backing_type: obj,
        count_member: obj,
    ) -> None:
        """Initialize the VLA.

        Unlike array_impl, the count is not a fixed integer but a reference
        to a sibling struct member that is read on every access.
        """
        # Skip array_impl.__init__ — it stores a fixed _count.
        # Call array (grandparent) init only.
        array.__init__(self, resolver)
        self.backing_type = backing_type
        self._count_member = count_member
        self.item_size = size_of(backing_type)

    @property  # type: ignore[override]
    def _count(self: vla_impl) -> int:
        """Read the current element count from the sibling field."""
        count = self._count_member.value

        if not isinstance(count, int):
            raise TypeError(
                f"VLA count field must be an integer type, got {type(count).__name__}",
            )

        if count < 0:
            raise ValueError(
                f"VLA count field must be non-negative, got {count}",
            )

        return count

    @_count.setter
    def _count(self: vla_impl, _: int) -> None:
        """No-op — count is always derived from the sibling member."""

    @property  # type: ignore[override]
    def size(self: vla_impl) -> int:
        """Return the current byte size of the VLA data."""
        return self.item_size * self._count

    @size.setter
    def size(self: vla_impl, _: int) -> None:
        """No-op — size is always derived from count."""
