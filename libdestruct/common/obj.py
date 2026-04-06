#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from libdestruct.common.hexdump import format_hexdump

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver

T = TypeVar("T")

class obj(ABC, Generic[T]):
    """A generic object, with reference to the backing memory view."""

    endianness: Literal["little", "big"] = "little"
    """The endianness of the backing reference view."""

    resolver: Resolver
    """The backing storage that resolves to this instance of a type."""

    _frozen: bool = False
    """Whether the object is frozen."""

    _frozen_value: object = None
    """The frozen value of the object."""

    def __init__(self: obj, resolver: Resolver | None) -> None:
        """Initialize a generic object.

        Args:
            resolver: The resolver for the value of this object.
        """
        self.resolver = resolver
        if resolver is not None:
            self.endianness = resolver.endianness

    @property
    def address(self: obj) -> int:
        """Return the address of the object in the memory view."""
        return self.resolver.resolve_address()

    @abstractmethod
    def get(self: obj) -> object:
        """Return the value of the object."""

    @abstractmethod
    def _set(self: obj, value: object) -> None:
        """Set the value of the object to the given value."""

    @abstractmethod
    def to_bytes(self: obj) -> bytes:
        """Serialize the object to bytes."""

    @classmethod
    def from_bytes(cls: type[obj], data: bytes, endianness: Literal["little", "big"] = "little") -> obj:
        """Deserialize the object from bytes."""
        from libdestruct.libdestruct import inflater

        lib = inflater(data, endianness=endianness)
        item = lib.inflate(cls, 0)
        item.freeze()
        return item

    def set(self: obj, value: object) -> None:
        """Set the value of the object to the given value."""
        if self._frozen:
            raise ValueError("Cannot set the value of a frozen object.")

        self._set(value)

    def freeze(self: obj) -> None:
        """Freeze the object."""
        object.__setattr__(self, "_frozen_value", self.get())
        object.__setattr__(self, "_frozen", True)

    def diff(self: obj) -> tuple[object, object]:
        """Return the difference between the current value and the frozen value."""
        try:
            return self._frozen_value, self.get()
        except ValueError as e:
            raise RuntimeError("Could not calculate the diff the object.") from e

    def reset(self: obj) -> None:
        """Reset the object to its frozen value."""
        try:
            self._set(self._frozen_value)
        except ValueError as e:
            raise RuntimeError("Could not reset the object to its frozen value.") from e

    def update(self: obj) -> None:
        """Update the object with the given value."""
        try:
            object.__setattr__(self, "_frozen_value", self.get())
        except ValueError as e:
            raise RuntimeError("Could not update the object.") from e

    @property
    def value(self: obj) -> object:
        """Return the value of the object."""
        if self._frozen:
            return self._frozen_value
        return self.get()

    @value.setter
    def value(self: obj, value: object) -> None:
        """Set the value of the object to the given value."""
        if self._frozen:
            raise ValueError("Cannot set the value of a frozen object.")

        self._set(value)

    def to_str(self: obj, _: int = 0) -> str:
        """Return a string representation of the object."""
        return f"{self.get()}"

    def pdiff(self: obj) -> str:
        """Return a string representation of the difference between the current value and the frozen value."""
        return f"{self._frozen_value} -> {self.get()}"

    def __str__(self: obj) -> str:
        """Return a string representation of the object."""
        return self.to_str()

    def __repr__(self: obj) -> str:
        """Return a string representation of the object."""
        return f"{self.__class__.__name__}({self.get()})"

    def _compare_value(self: obj, other: object) -> tuple[object, object] | None:
        """Extract comparable values from self and other, or None if incompatible."""
        self_val = self.value
        if isinstance(other, obj):
            other_val = other.value
            # Guard against incompatible value types (e.g. int vs str from struct.get())
            if type(self_val) is not type(other_val) and not isinstance(self_val, type(other_val)) and not isinstance(other_val, type(self_val)):
                return None
            return self_val, other_val
        if isinstance(other, int | float | bytes):
            return self_val, other
        return None

    def __eq__(self: obj, other: object) -> bool:
        """Return whether the object is equal to the given value."""
        pair = self._compare_value(other)
        if pair is None:
            return NotImplemented
        return pair[0] == pair[1]

    def __ne__(self: obj, other: object) -> bool:
        """Return whether the object is not equal to the given value."""
        pair = self._compare_value(other)
        if pair is None:
            return NotImplemented
        return pair[0] != pair[1]

    def __lt__(self: obj, other: object) -> bool:
        """Return whether this object is less than the given value."""
        pair = self._compare_value(other)
        if pair is None:
            return NotImplemented
        return pair[0] < pair[1]

    def __le__(self: obj, other: object) -> bool:
        """Return whether this object is less than or equal to the given value."""
        pair = self._compare_value(other)
        if pair is None:
            return NotImplemented
        return pair[0] <= pair[1]

    def __gt__(self: obj, other: object) -> bool:
        """Return whether this object is greater than the given value."""
        pair = self._compare_value(other)
        if pair is None:
            return NotImplemented
        return pair[0] > pair[1]

    def __ge__(self: obj, other: object) -> bool:
        """Return whether this object is greater than or equal to the given value."""
        pair = self._compare_value(other)
        if pair is None:
            return NotImplemented
        return pair[0] >= pair[1]

    def to_dict(self: obj) -> object:
        """Return a JSON-serializable representation of the object."""
        return self.value

    def hexdump(self: obj) -> str:
        """Return a hex dump of this object's bytes."""
        address = self.address if not self._frozen else 0
        return format_hexdump(self.to_bytes(), address)

    def __bytes__(self: obj) -> bytes:
        """Return the serialized object."""
        return self.to_bytes()
