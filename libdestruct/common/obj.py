#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver

T = TypeVar("T")

class obj(ABC, Generic[T]):
    """A generic object, with reference to the backing memory view."""

    endianness: str = "little"
    """The endianness of the backing reference view."""

    resolver: Resolver
    """The backing storage that resolves to this instance of a type."""

    _frozen: bool = False
    """Whether the object is frozen."""

    _frozen_value: object = None
    """The frozen value of the object."""

    def __init__(self: obj, resolver: Resolver) -> None:
        """Initialize a generic object.

        Args:
            resolver: The resolver for the value of this object.
        """
        self.resolver = resolver

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
    def from_bytes(cls: type[obj], data: bytes) -> obj:
        """Deserialize the object from bytes."""
        from libdestruct.libdestruct import inflater

        lib = inflater(data)
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
        self._frozen_value = self.get()
        self._frozen = True

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
            self._frozen_value = self.get()
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

    def __eq__(self: obj, value: object) -> bool:
        """Return whether the object is equal to the given value."""
        if not isinstance(value, obj):
            return False

        return self.get() == value.get()

    def __bytes__(self: obj) -> bytes:
        """Return the serialized object."""
        return self.to_bytes()
