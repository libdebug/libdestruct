#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from types import GenericAlias
from typing import TYPE_CHECKING

from libdestruct.common.obj import obj
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from enum import IntFlag

    from libdestruct.backing.resolver import Resolver


class flags(obj):
    """A generic bit flags field."""

    def __class_getitem__(cls, params: tuple) -> GenericAlias:
        """Support flags[MyFlags] and flags[MyFlags, c_short] subscript syntax."""
        if not isinstance(params, tuple):
            params = (params,)
        return GenericAlias(cls, params)

    python_flag: type[IntFlag]
    """The backing Python IntFlag."""

    _backing_type: obj
    """The inflated backing instance."""

    lenient: bool
    """Whether the conversion is lenient or not."""

    def __init__(
        self: flags,
        resolver: Resolver,
        python_flag: type[IntFlag],
        backing_type: type[obj],
        lenient: bool = True,
    ) -> None:
        """Initialize the flags object."""
        super().__init__(resolver)

        self.python_flag = python_flag
        self._backing_type = TypeRegistry().inflater_for(backing_type)(resolver)
        self.lenient = lenient

        self.size = self._backing_type.size

    def get(self: flags) -> IntFlag:
        """Return the value of the flags."""
        raw = self._backing_type.get()
        if not self.lenient:
            # Compute the mask of all defined flag bits
            all_bits = 0
            for member in self.python_flag:
                all_bits |= member.value
            if raw & ~all_bits:
                raise ValueError(
                    f"Unknown bits 0x{raw & ~all_bits:x} in {self.python_flag.__name__}({raw!r})"
                )
        return self.python_flag(raw)

    def _set(self: flags, value: IntFlag) -> None:
        """Set the value of the flags."""
        self._backing_type.set(int(value))

    def to_bytes(self: flags) -> bytes:
        """Return the serialized representation of the flags."""
        return self._backing_type.to_bytes()

    def to_str(self: obj, indent: int = 0) -> str:
        """Return a string representation of the object."""
        return f"{self.get()!r}"
