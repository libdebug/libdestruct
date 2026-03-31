#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.obj import obj

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver


class bitfield(obj):
    """A bitfield within a backing integer type."""

    _backing_instance: obj
    """The inflated backing integer instance (shared with sibling bitfields)."""

    _bit_offset: int
    """The starting bit position within the backing integer."""

    _bit_width: int
    """The number of bits this field occupies."""

    _signed: bool
    """Whether to sign-extend when reading."""

    _is_group_owner: bool
    """Whether this bitfield owns the backing bytes (first in its group)."""

    def __init__(
        self: bitfield,
        resolver: Resolver,
        backing_instance: obj,
        bit_offset: int,
        bit_width: int,
        signed: bool,
        is_group_owner: bool,
    ) -> None:
        """Initialize the bitfield.

        Args:
            resolver: The backing resolver.
            backing_instance: The already-inflated backing integer (shared across bitfields in the same group).
            bit_offset: The starting bit position within the backing integer.
            bit_width: The number of bits this field occupies.
            signed: Whether to sign-extend when reading.
            is_group_owner: Whether this bitfield is the first in its group (owns the backing bytes).
        """
        super().__init__(resolver)
        self._backing_instance = backing_instance
        self._bit_offset = bit_offset
        self._bit_width = bit_width
        self._signed = signed
        self._mask = (1 << bit_width) - 1
        self._is_group_owner = is_group_owner
        # Owner reports the full backing size; non-owners report 0
        self.size = backing_instance.size if is_group_owner else 0

    def get(self: bitfield) -> int:
        """Return the value of the bitfield."""
        raw = self._backing_instance.get()
        # For signed backing types, raw may be negative. Work with unsigned representation.
        if raw < 0:
            raw += 1 << (self._backing_instance.size * 8)
        value = (raw >> self._bit_offset) & self._mask
        if self._signed and (value >> (self._bit_width - 1)) & 1:
            value -= 1 << self._bit_width
        return value

    def _set(self: bitfield, value: int) -> None:
        """Set the value of the bitfield."""
        masked_value = value & self._mask
        raw = self._backing_instance.get()
        if raw < 0:
            raw += 1 << (self._backing_instance.size * 8)
        raw = (raw & ~(self._mask << self._bit_offset)) | (masked_value << self._bit_offset)
        total_bits = self._backing_instance.size * 8
        is_signed = hasattr(self._backing_instance, "signed") and self._backing_instance.signed
        if is_signed and raw >= (1 << (total_bits - 1)):
            raw -= 1 << total_bits
        self._backing_instance._set(raw)

    def to_bytes(self: bitfield) -> bytes:
        """Return the serialized representation of the backing type.

        Only the group owner emits bytes; non-owners return empty bytes
        to avoid duplication when the struct serializes all members.
        """
        if self._is_group_owner:
            return self._backing_instance.to_bytes()
        return b""

    def to_str(self: bitfield, _: int = 0) -> str:
        """Return a string representation of the bitfield."""
        return f"{self.get()}"
