#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import Any

from libdestruct.common.obj import obj


class _ctypes_generic(obj):
    """A generic holder for a ctypes object."""

    size: int
    """The size of the type in bytes."""

    _frozen_value: bytes | None = None
    """The frozen value of the type."""

    backing_type: type
    """The backing ctypes object."""

    def get(self: _ctypes_generic) -> Any:
        """Return the value of the type."""
        return self.backing_type.from_buffer_copy(self.resolver.resolve(self.size, 0)).value

    def _set(self: _ctypes_generic, value: Any) -> None:
        """Set the value of the type to the given value."""
        self.resolver.modify(self.size, 0, bytes(self.backing_type(value)))

    def to_bytes(self: _ctypes_generic) -> bytes:
        """Serialize the type to bytes."""
        if self._frozen:
            return bytes(self.backing_type(self._frozen_value))

        return self.resolver.resolve(self.size, 0)
