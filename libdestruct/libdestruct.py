#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import mmap
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from libdestruct.backing.resolver import Resolver
from libdestruct.common.inflater import Inflater

if TYPE_CHECKING:  # pragma: no cover
    import io

    from libdestruct.common.obj import obj


_VALID_ENDIANNESS = ("little", "big")


def inflater(memory: Sequence | mmap.mmap, endianness: Literal["little", "big"] = "little") -> Inflater:
    """Return a TypeInflater instance."""
    if not isinstance(memory, Sequence | mmap.mmap):
        raise TypeError(f"memory must be a Sequence, not {type(memory).__name__}")

    if endianness not in _VALID_ENDIANNESS:
        raise ValueError(f"endianness must be 'little' or 'big', not {endianness!r}")

    return Inflater(memory, endianness=endianness)


class FileInflater(Inflater):
    """An inflater backed by a memory-mapped file."""

    def __init__(
        self: FileInflater,
        file_handle: io.BufferedReader,
        mmap_obj: mmap.mmap,
        endianness: Literal["little", "big"] = "little",
    ) -> None:
        """Initialize the file-backed inflater."""
        super().__init__(mmap_obj, endianness=endianness)
        self._file_handle = file_handle
        self._mmap = mmap_obj

    def __enter__(self: FileInflater) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self: FileInflater, *args: object) -> None:
        """Close mmap and file handle."""
        self._mmap.close()
        self._file_handle.close()


def inflater_from_file(path: str, writable: bool = False, endianness: Literal["little", "big"] = "little") -> FileInflater:
    """Create an inflater backed by a memory-mapped file.

    Args:
        path: Path to the binary file.
        writable: If True, writes through the inflater are persisted to the file.
        endianness: The byte order ("little" or "big").

    Returns:
        A FileInflater context manager.
    """
    if endianness not in _VALID_ENDIANNESS:
        raise ValueError(f"endianness must be 'little' or 'big', not {endianness!r}")

    mode = "r+b" if writable else "rb"
    access = mmap.ACCESS_WRITE if writable else mmap.ACCESS_READ
    file_handle = Path(path).open(mode)  # noqa: SIM115 — managed by FileInflater.__exit__
    mmap_obj = mmap.mmap(file_handle.fileno(), 0, access=access)
    return FileInflater(file_handle, mmap_obj, endianness=endianness)


def inflate(item: type, memory: Sequence, address: int | Resolver, endianness: Literal["little", "big"] = "little") -> obj:
    """Inflate a memory-referencing type.

    Args:
        item: The type to inflate.
        memory: The memory view, which can be mutable or immutable.
        address: The address of the object in the memory view.
        endianness: The byte order ("little" or "big").

    Returns:
        The inflated object.
    """
    if not isinstance(address, int) and not isinstance(address, Resolver):
        raise TypeError(f"address must be an int or a Resolver, not {type(address).__name__}")

    return inflater(memory, endianness=endianness).inflate(item, address)
