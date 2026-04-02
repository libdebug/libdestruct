#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from types import GenericAlias
from typing import Annotated, get_args, get_origin

from typing_extensions import Self

from libdestruct.backing.fake_resolver import FakeResolver
from libdestruct.backing.resolver import Resolver
from libdestruct.common.array.vla_field import VLAField
from libdestruct.common.attributes.offset_attribute import OffsetAttribute
from libdestruct.common.bitfield.bitfield_field import BitfieldField
from libdestruct.common.bitfield.bitfield_tracker import BitfieldTracker
from libdestruct.common.field import Field
from libdestruct.common.hexdump import format_hexdump
from libdestruct.common.obj import obj
from libdestruct.common.struct import struct
from libdestruct.common.type_registry import TypeRegistry
from libdestruct.common.utils import _align_offset, alignment_of, iterate_annotation_chain, size_of


class struct_impl(struct):
    """The implementation for the C struct type."""

    _members: dict[str, obj]
    """The members of the struct."""

    _reference_struct: struct
    """The reference struct."""

    _inflater: TypeRegistry = TypeRegistry()
    """The type registry, used for inflating the attributes."""

    def __init__(self: struct_impl, resolver: Resolver | None = None, **kwargs: ...) -> None:
        """Initialize the struct implementation."""
        # If we have kwargs and the resolver is None, we provide a fake resolver
        if kwargs and resolver is None:
            resolver = FakeResolver()

        if not isinstance(resolver, Resolver):
            raise TypeError("The resolver must be a Resolver instance.")

        # struct overrides the __init__ method, so we need to call the parent class __init__ method
        obj.__init__(self, resolver)

        object.__setattr__(self, "_struct_name", self.__class__.__name__)
        object.__setattr__(self, "_members", {})

        reference_type = self._reference_struct
        self._inflate_struct_attributes(self._inflater, resolver, reference_type)

        for name, value in kwargs.items():
            getattr(self, name).value = value

    def __getattribute__(self: struct_impl, name: str) -> object:
        """Return the attribute, checking struct members first to avoid collisions with obj properties."""
        # Check _members dict directly to avoid infinite recursion
        try:
            members = object.__getattribute__(self, "_members")
            if name in members:
                return members[name]
        except AttributeError:
            pass
        return super().__getattribute__(name)

    def __setattr__(self: struct_impl, name: str, value: object) -> None:
        """Set an attribute, delegating to member.value for struct fields."""
        try:
            members = object.__getattribute__(self, "_members")
            if name in members:
                members[name].value = value
                return
        except AttributeError:
            pass
        object.__setattr__(self, name, value)

    def __new__(cls: struct_impl, *args: ..., **kwargs: ...) -> Self:
        """Create a new struct."""
        # Skip the __new__ method of the parent class
        # struct_impl -> struct -> obj becomes struct_impl -> obj
        return obj.__new__(cls)

    def _inflate_struct_attributes(
        self: struct_impl,
        inflater: TypeRegistry,
        resolver: Resolver,
        reference_type: type,
    ) -> None:
        current_offset = 0
        max_alignment = 1
        bf_tracker = BitfieldTracker()
        aligned = getattr(reference_type, "_aligned_", False)
        object.__setattr__(self, "_member_offsets", {})

        for name, annotation, reference in iterate_annotation_chain(reference_type, terminate_at=struct):
            if name == "_aligned_":
                continue

            resolved_type, bitfield_field, explicit_offset = struct_impl._resolve_field(
                name, annotation, reference, inflater, owner=(self, reference_type._type_impl),
            )

            if explicit_offset is not None:
                current_offset += bf_tracker.flush()
                if explicit_offset < current_offset:
                    raise ValueError("Offset must be greater than the current size.")
                current_offset = explicit_offset

            if bitfield_field:
                if aligned and bf_tracker.needs_new_group(bitfield_field):
                    current_offset += bf_tracker.flush()
                    field_align = alignment_of(bitfield_field.backing_type)
                    max_alignment = max(max_alignment, field_align)
                    current_offset = _align_offset(current_offset, field_align)
                self._member_offsets[name] = current_offset
                result, offset_delta = bf_tracker.create_bitfield(
                    bitfield_field, inflater, resolver, current_offset,
                )
                current_offset += offset_delta
            else:
                current_offset += bf_tracker.flush()
                if aligned and explicit_offset is None:
                    # Try alignment from the resolved type directly; for closures
                    # (e.g. union inflaters) alignment_of can't inspect them, so
                    # fall back to creating a probe instance.
                    field_align = alignment_of(resolved_type)
                    if field_align <= 1:
                        try:
                            probe = resolved_type(resolver.relative_from_own(current_offset, 0))
                            field_align = alignment_of(probe)
                        except (ValueError, TypeError):
                            pass
                    max_alignment = max(max_alignment, field_align)
                    current_offset = _align_offset(current_offset, field_align)
                self._member_offsets[name] = current_offset
                result = resolved_type(resolver.relative_from_own(current_offset, 0))
                current_offset += size_of(result)

            self._members[name] = result

        current_offset += bf_tracker.flush()

        # Apply tail padding for aligned structs
        if aligned:
            if isinstance(aligned, int) and aligned is not True:
                max_alignment = max(max_alignment, aligned)
            current_offset = _align_offset(current_offset, max_alignment)

        # For VLA structs, size must be computed dynamically since the count
        # can change at runtime.  Detect VLA by duck-typing: vla_impl has a
        # _count_member attribute that plain array_impl does not.
        members = object.__getattribute__(self, "_members")
        last_member = list(members.values())[-1] if members else None
        if last_member is not None and hasattr(last_member, "_count_member"):
            last_name = list(members.keys())[-1]
            object.__setattr__(self, "_vla_fixed_offset", self._member_offsets[last_name])
        else:
            object.__setattr__(self, "size", current_offset)

    @staticmethod
    def _resolve_field(
        name: str,
        annotation: type,
        reference: type,
        inflater: TypeRegistry,
        owner: tuple[obj, type] | None,
    ) -> tuple[object | None, BitfieldField | None, int | None]:
        """Resolve a single struct field annotation to its inflater or BitfieldField.

        Returns:
            A tuple of (resolved_inflater, bitfield_field, explicit_offset).
            Either resolved_inflater or bitfield_field will be non-None (not both).
            explicit_offset is set when an OffsetAttribute is present.
        """
        # Unwrap Annotated[type, metadata...] — extract the real type and any metadata
        annotated_offset = None
        if get_origin(annotation) is Annotated:
            ann_args = get_args(annotation)
            annotation = ann_args[0]
            for meta in ann_args[1:]:
                if isinstance(meta, OffsetAttribute):
                    annotated_offset = meta.offset

        if name not in reference.__dict__:
            return inflater.inflater_for(annotation, owner=owner), None, annotated_offset

        attrs = getattr(reference, name)
        if not isinstance(attrs, tuple):
            attrs = (attrs,)

        if sum(isinstance(attr, Field) for attr in attrs) > 1:
            raise ValueError("Only one Field is allowed per attribute.")

        resolved_type = None
        bitfield_field = None
        explicit_offset = annotated_offset

        for attr in attrs:
            if isinstance(attr, BitfieldField):
                bitfield_field = attr
            elif isinstance(attr, Field):
                resolved_type = inflater.inflater_for(
                    (attr, annotation), owner=owner,
                )
            elif isinstance(attr, OffsetAttribute):
                explicit_offset = attr.offset
            else:
                raise TypeError("Only Field, BitfieldField, and OffsetAttribute are allowed in attributes.")

        if not resolved_type and not bitfield_field:
            resolved_type = inflater.inflater_for(annotation, owner=owner)

        return resolved_type, bitfield_field, explicit_offset

    @classmethod
    def compute_own_size(cls: type[struct_impl], reference_type: type) -> None:
        """Compute the size of the struct."""
        size = 0
        max_alignment = 1
        bf_tracker = BitfieldTracker()
        aligned = getattr(reference_type, "_aligned_", False)
        seen_vla = False

        for name, annotation, reference in iterate_annotation_chain(reference_type, terminate_at=struct):
            if name == "_aligned_":
                continue

            # VLA must be the last field
            if seen_vla:
                raise ValueError(
                    f"Variable-length array must be the last field in a struct. "
                    f"Field '{name}' follows a VLA."
                )
            # Detect VLA from default value or subscript annotation
            default = getattr(reference, name, None) if hasattr(reference, name) else None
            is_vla = isinstance(default, VLAField)
            if not is_vla and isinstance(annotation, GenericAlias):
                args = annotation.__args__
                if len(args) == 2 and isinstance(args[1], str):
                    is_vla = True
            if is_vla:
                seen_vla = True

            resolved_type, bitfield_field, explicit_offset = struct_impl._resolve_field(
                name, annotation, reference, cls._inflater, owner=(None, cls),
            )

            has_explicit_offset = explicit_offset is not None
            if has_explicit_offset:
                size += bf_tracker.flush()
                if explicit_offset < size:
                    raise ValueError("Offset must be greater than the current size.")
                size = explicit_offset

            if bitfield_field:
                if aligned and bf_tracker.needs_new_group(bitfield_field):
                    size += bf_tracker.flush()
                    field_align = alignment_of(bitfield_field.backing_type)
                    max_alignment = max(max_alignment, field_align)
                    size = _align_offset(size, field_align)
                size += bf_tracker.compute_size(bitfield_field)
            else:
                size += bf_tracker.flush()
                # Get attribute for size computation — try size_of directly first,
                # falling back to calling the inflater with None for complex fields.
                # Direct size_of avoids recursion for forward-ref pointers.
                try:
                    attribute_size = size_of(resolved_type)
                    attribute = resolved_type
                except (ValueError, TypeError):
                    attribute = resolved_type(None)
                    attribute_size = size_of(attribute)
                if aligned and not has_explicit_offset:
                    field_align = alignment_of(attribute)
                    max_alignment = max(max_alignment, field_align)
                    size = _align_offset(size, field_align)
                size += attribute_size

        size += bf_tracker.flush()

        if aligned:
            if isinstance(aligned, int) and aligned is not True:
                max_alignment = max(max_alignment, aligned)
            size = _align_offset(size, max_alignment)

        cls.size = size
        cls.alignment = max_alignment if aligned else 1

    @property
    def address(self: struct_impl) -> int:
        """Return the address of the struct, bypassing __getattribute__ to avoid member collisions."""
        resolver = object.__getattribute__(self, "resolver")
        return resolver.resolve_address()

    def get(self: struct_impl) -> str:
        """Return the value of the struct."""
        name = object.__getattribute__(self, "_struct_name")
        addr = struct_impl.address.fget(self)
        return f"{name}(address={addr}, size={size_of(self)})"

    def to_bytes(self: struct_impl) -> bytes:
        """Return the serialized representation of the struct, including padding."""
        if object.__getattribute__(self, "_frozen"):
            return object.__getattribute__(self, "_frozen_struct_bytes")
        resolver = object.__getattribute__(self, "resolver")
        return resolver.resolve(size_of(self), 0)

    def to_dict(self: struct_impl) -> dict[str, object]:
        """Return a JSON-serializable dict of field names to values."""
        members = object.__getattribute__(self, "_members")
        return {name: member.to_dict() for name, member in members.items()}

    def hexdump(self: struct_impl) -> str:
        """Return a hex dump of this struct's bytes with field annotations."""
        member_offsets = object.__getattribute__(self, "_member_offsets")
        members = object.__getattribute__(self, "_members")
        annotations: dict[int, str] = {}
        for name in members:
            off = member_offsets[name]
            if off in annotations:
                annotations[off] += ", " + name
            else:
                annotations[off] = name
        address = struct_impl.address.fget(self) if not object.__getattribute__(self, "_frozen") else 0
        return format_hexdump(self.to_bytes(), address, annotations)

    def _set(self: struct_impl, _: str) -> None:
        """Set the value of the struct to the given value."""
        raise RuntimeError("Cannot set the value of a struct.")

    def freeze(self: struct_impl) -> None:
        """Freeze the struct, capturing the full byte representation including padding."""
        resolver = object.__getattribute__(self, "resolver")
        object.__setattr__(self, "_frozen_struct_bytes", resolver.resolve(size_of(self), 0))

        members = object.__getattribute__(self, "_members")
        for member in members.values():
            member.freeze()

        super().freeze()

    def reset(self: struct_impl) -> None:
        """Reset each member to its frozen value."""
        if not object.__getattribute__(self, "_frozen"):
            raise RuntimeError("Cannot reset a struct that has not been frozen.")

        members = object.__getattribute__(self, "_members")
        for member in members.values():
            member.reset()

    def to_str(self: struct_impl, indent: int = 0) -> str:
        """Return a string representation of the struct."""
        name = object.__getattribute__(self, "_struct_name")
        members_dict = object.__getattribute__(self, "_members")
        members = ",\n".join(
            [f"{' ' * (indent + 4)}{n}: {member.to_str(indent + 4)}" for n, member in members_dict.items()],
        )
        return f"""{name} {{
{members}
{" " * indent}}}"""

    def __repr__(self: struct_impl) -> str:
        """Return a string representation of the struct."""
        name = object.__getattribute__(self, "_struct_name")
        addr = struct_impl.address.fget(self)
        members_dict = object.__getattribute__(self, "_members")
        members = ",\n".join([f"{n}: {member}" for n, member in members_dict.items()])
        return f"""{name} {{
    address: 0x{addr:x},
    size: 0x{size_of(self):x},
    members: {{
        {members}
    }}
}}"""

    def __eq__(self: struct_impl, value: object) -> bool:
        """Return whether the struct is equal to the given value."""
        if not isinstance(value, struct_impl):
            return NotImplemented

        if size_of(self) != size_of(value):
            return False

        self_members = object.__getattribute__(self, "_members")
        other_members = object.__getattribute__(value, "_members")

        if self_members.keys() != other_members.keys():
            return False

        return all(getattr(self, name) == getattr(value, name) for name in self_members)
