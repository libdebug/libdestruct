#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct.common.bitfield.bitfield import bitfield

if TYPE_CHECKING:  # pragma: no cover
    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.bitfield.bitfield_field import BitfieldField
    from libdestruct.common.obj import obj
    from libdestruct.common.type_registry import TypeRegistry


class BitfieldTracker:
    """Tracks bitfield group state during struct field inflation.

    Consecutive bitfields with the same backing type are packed into a shared
    backing integer instance. This class manages the grouping, bit offset
    tracking, and byte offset advancement.
    """

    def __init__(self: BitfieldTracker) -> None:
        """Initialize the tracker with no active group."""
        self._bit_offset: int = 0
        self._backing_type: type | None = None
        self._backing_instance: obj | None = None

    @property
    def active(self: BitfieldTracker) -> bool:
        """Return whether a bitfield group is currently active."""
        return self._backing_type is not None

    def needs_new_group(self: BitfieldTracker, field: BitfieldField) -> bool:
        """Return whether the given field would start a new bitfield group."""
        return (
            self._backing_type is not field.backing_type
            or self._bit_offset + field.bit_width > field.backing_type.size * 8
        )

    def flush(self: BitfieldTracker) -> int:
        """Close the current bitfield group and return the byte size to advance.

        Returns:
            The backing type's byte size if a group was active, 0 otherwise.
        """
        if self._backing_type is not None:
            size = self._backing_type.size
            self._backing_type = None
            self._backing_instance = None
            self._bit_offset = 0
            return size
        return 0

    def create_bitfield(
        self: BitfieldTracker,
        field: BitfieldField,
        inflater: TypeRegistry,
        resolver: Resolver,
        current_offset: int,
    ) -> tuple[bitfield, int]:
        """Create a bitfield instance, managing group transitions.

        Args:
            field: The BitfieldField descriptor.
            inflater: The type registry for inflating the backing type.
            resolver: The struct's resolver.
            current_offset: The current byte offset in the struct.

        Returns:
            A tuple of (bitfield_instance, byte_offset_delta).
            The delta is nonzero only when a new group starts (flushing the old one).
        """
        backing_type = field.backing_type
        bit_width = field.bit_width
        backing_size_bits = backing_type.size * 8
        offset_delta = 0

        # Start a new group if the backing type changed or bits would overflow
        if self._backing_type is not backing_type or self._bit_offset + bit_width > backing_size_bits:
            offset_delta = self.flush()
            self._backing_type = backing_type
            self._backing_instance = inflater.inflater_for(backing_type)(
                resolver.relative_from_own(current_offset + offset_delta, 0),
            )

        is_owner = self._bit_offset == 0
        signed = getattr(backing_type, "signed", False)

        result = bitfield(
            resolver.relative_from_own(current_offset + offset_delta, 0),
            self._backing_instance,
            self._bit_offset,
            bit_width,
            signed,
            is_owner,
        )
        self._bit_offset += bit_width
        return result, offset_delta

    def compute_size(self: BitfieldTracker, field: BitfieldField) -> int:
        """Account for a bitfield during size computation, without inflating.

        Args:
            field: The BitfieldField descriptor.

        Returns:
            The byte size delta (nonzero only when a new group starts).
        """
        backing_type = field.backing_type
        bit_width = field.bit_width
        backing_size_bits = backing_type.size * 8
        size_delta = 0

        if self._backing_type is not backing_type or self._bit_offset + bit_width > backing_size_bits:
            size_delta = self.flush()
            self._backing_type = backing_type

        self._bit_offset += bit_width
        return size_delta
