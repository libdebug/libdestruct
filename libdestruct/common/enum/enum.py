#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from types import GenericAlias
from typing import TYPE_CHECKING

from libdestruct.common.obj import obj
from libdestruct.common.type_registry import TypeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from enum import Enum

    from libdestruct.backing.resolver import Resolver


class enum(obj):
    """A generic enum."""

    def __class_getitem__(cls, params: tuple) -> GenericAlias:
        """Support enum[MyEnum] and enum[MyEnum, c_short] subscript syntax."""
        if not isinstance(params, tuple):
            params = (params,)
        return GenericAlias(cls, params)

    python_enum: type[Enum]
    """The backing Python enum."""

    _backing_type: type[obj]
    """The backing type."""

    lenient: bool
    """Whether the conversion is lenient or not."""

    def __init__(
        self: enum,
        resolver: Resolver,
        python_enum: type[Enum],
        backing_type: type[obj],
        lenient: bool = True,
    ) -> None:
        """Initialize the enum object."""
        super().__init__(resolver)

        self.python_enum = python_enum
        self._backing_type = TypeRegistry().inflater_for(backing_type)(resolver)
        self.lenient = lenient

        self.size = self._backing_type.size

    def get(self: enum) -> Enum:
        """Return the value of the enum."""
        return self.python_enum(self._backing_type.get())

    def _set(self: enum, value: Enum) -> None:
        """Set the value of the enum."""
        self._backing_type.set(value.value)

    def to_bytes(self: enum) -> bytes:
        """Return the serialized representation of the enum."""
        return self._backing_type.to_bytes()

    def to_str(self: obj, indent: int = 0) -> str:
        """Return a string representation of the object."""
        return f"{self.get()!r}"
