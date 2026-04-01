#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from abc import abstractmethod
from types import GenericAlias

from libdestruct.common.obj import obj


class array(obj):
    """An array of objects."""

    def __class_getitem__(cls, params: tuple) -> GenericAlias:
        """Support array[c_int, 3] subscript syntax."""
        if not isinstance(params, tuple):
            params = (params,)
        return GenericAlias(cls, params)

    @abstractmethod
    def count(self: array) -> int:
        """Return the size of the array."""

    def __len__(self: array) -> int:
        """Return the size of the array."""
        return self.count()

    @abstractmethod
    def get(self: array, index: int = -1) -> object:
        """Return the element at the given index, or all elements if index is -1."""

    def __getitem__(self: array, index: int) -> object:
        """Return the element at the given index."""
        return self.get(index)

    def __setitem__(self: array, index: int, value: object) -> None:
        """Set the element at the given index to the given value."""
        self.set(index, value)

    @abstractmethod
    def __iter__(self: array) -> iter:
        """Return an iterator over the array."""

    def __contains__(self: array, value: object) -> bool:
        """Return whether the array contains the given value."""
        return any(value == element for element in self)
