#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing_extensions import Self

from libdestruct.backing.fake_resolver import FakeResolver
from libdestruct.backing.resolver import Resolver
from libdestruct.common.attributes.offset_attribute import OffsetAttribute
from libdestruct.common.bitfield.bitfield_field import BitfieldField
from libdestruct.common.bitfield.bitfield_tracker import BitfieldTracker
from libdestruct.common.field import Field
from libdestruct.common.obj import obj
from libdestruct.common.struct import struct
from libdestruct.common.type_registry import TypeRegistry
from libdestruct.common.utils import iterate_annotation_chain, size_of


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

        self._struct_name = self.__class__.__name__
        self._members = {}

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
        bf_tracker = BitfieldTracker()

        for name, annotation, reference in iterate_annotation_chain(reference_type, terminate_at=struct):
            resolved_type, bitfield_field, explicit_offset = self._resolve_field(
                name, annotation, reference, inflater, reference_type,
            )

            if explicit_offset is not None:
                if explicit_offset < current_offset:
                    raise ValueError("Offset must be greater than the current size.")
                current_offset = explicit_offset

            if bitfield_field:
                result, offset_delta = bf_tracker.create_bitfield(
                    bitfield_field, inflater, resolver, current_offset,
                )
                current_offset += offset_delta
            else:
                current_offset += bf_tracker.flush()
                result = resolved_type(resolver.relative_from_own(current_offset, 0))
                current_offset += size_of(result)

            self._members[name] = result

        current_offset += bf_tracker.flush()

    def _resolve_field(
        self: struct_impl,
        name: str,
        annotation: type,
        reference: type,
        inflater: TypeRegistry,
        reference_type: type,
    ) -> tuple[object | None, BitfieldField | None, int | None]:
        """Resolve a single struct field annotation to its inflater or BitfieldField.

        Returns:
            A tuple of (resolved_inflater, bitfield_field, explicit_offset).
            Either resolved_inflater or bitfield_field will be non-None (not both).
            explicit_offset is set when an OffsetAttribute is present.
        """
        if name not in reference.__dict__:
            return inflater.inflater_for(annotation, owner=(self, reference_type._type_impl)), None, None

        attrs = getattr(reference, name)
        if not isinstance(attrs, tuple):
            attrs = (attrs,)

        if sum(isinstance(attr, Field) for attr in attrs) > 1:
            raise ValueError("Only one Field is allowed per attribute.")

        resolved_type = None
        bitfield_field = None
        explicit_offset = None

        for attr in attrs:
            if isinstance(attr, BitfieldField):
                bitfield_field = attr
            elif isinstance(attr, Field):
                resolved_type = inflater.inflater_for(
                    (attr, annotation), owner=(self, reference_type._type_impl),
                )
            elif isinstance(attr, OffsetAttribute):
                explicit_offset = attr.offset
            else:
                raise TypeError("Only Field, BitfieldField, and OffsetAttribute are allowed in attributes.")

        if not resolved_type and not bitfield_field:
            resolved_type = inflater.inflater_for(annotation, owner=(self, reference_type._type_impl))

        return resolved_type, bitfield_field, explicit_offset

    @classmethod
    def compute_own_size(cls: type[struct_impl], reference_type: type) -> None:
        """Compute the size of the struct."""
        size = 0
        bf_tracker = BitfieldTracker()

        for name, annotation, reference in iterate_annotation_chain(reference_type, terminate_at=struct):
            bitfield_field = None
            attribute = None

            if name in reference.__dict__:
                attrs = getattr(reference, name)
                if not isinstance(attrs, tuple):
                    attrs = (attrs,)

                if sum(isinstance(attr, Field) for attr in attrs) > 1:
                    raise ValueError("Only one Field is allowed per attribute.")

                for attr in attrs:
                    if isinstance(attr, BitfieldField):
                        bitfield_field = attr
                    elif isinstance(attr, Field):
                        attribute = cls._inflater.inflater_for((attr, annotation), (None, cls))(None)
                    elif isinstance(attr, OffsetAttribute):
                        offset = attr.offset
                        if offset < size:
                            raise ValueError("Offset must be greater than the current size.")
                        size = offset

                if not attribute and not bitfield_field:
                    attribute = cls._inflater.inflater_for(annotation, (None, cls))
            elif isinstance(annotation, Field):
                attribute = cls._inflater.inflater_for((annotation, annotation.base_type), (None, cls))(None)
            else:
                attribute = cls._inflater.inflater_for(annotation, (None, cls))

            if bitfield_field:
                size += bf_tracker.compute_size(bitfield_field)
            else:
                size += bf_tracker.flush()
                size += size_of(attribute)

        size += bf_tracker.flush()
        cls.size = size

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
        """Return the serialized representation of the struct."""
        return b"".join(member.to_bytes() for member in self._members.values())

    def _set(self: struct_impl, _: str) -> None:
        """Set the value of the struct to the given value."""
        raise RuntimeError("Cannot set the value of a struct.")

    def freeze(self: struct_impl) -> None:
        """Freeze the struct."""
        # The struct has no implicit value, but it must freeze its members
        for member in self._members.values():
            member.freeze()

        self._frozen = True

    def to_str(self: struct_impl, indent: int = 0) -> str:
        """Return a string representation of the struct."""
        name = object.__getattribute__(self, "_struct_name")
        members = ",\n".join(
            [f"{' ' * (indent + 4)}{n}: {member.to_str(indent + 4)}" for n, member in self._members.items()],
        )
        return f"""{name} {{
{members}
{" " * indent}}}"""

    def __repr__(self: struct_impl) -> str:
        """Return a string representation of the struct."""
        name = object.__getattribute__(self, "_struct_name")
        addr = struct_impl.address.fget(self)
        members = ",\n".join([f"{n}: {member}" for n, member in self._members.items()])
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
            return False

        if size_of(self) != size_of(value):
            return False

        if not self._members.keys() == value._members.keys():
            return False

        return all(getattr(self, name) == getattr(value, name) for name in self._members)
