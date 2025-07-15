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

        self.name = self.__class__.__name__
        self._members = {}

        reference_type = self._reference_struct
        self._inflate_struct_attributes(self._inflater, resolver, reference_type)

        for name, value in kwargs.items():
            getattr(self, name).value = value

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

        for name, annotation, reference in iterate_annotation_chain(reference_type, terminate_at=struct):
            if name in reference.__dict__:
                # Field associated with the annotation
                attrs = getattr(reference, name)

                # If attrs is not a tuple, we need to convert it to a tuple
                if not isinstance(attrs, tuple):
                    attrs = (attrs,)

                # Assert that in all attributes, there is only one Field
                if sum(isinstance(attr, Field) for attr in attrs) > 1:
                    raise ValueError("Only one Field is allowed per attribute.")

                resolved_type = None

                for attr in attrs:
                    if isinstance(attr, Field):
                        resolved_type = inflater.inflater_for(
                            (attr, annotation),
                            owner=(self, reference_type._type_impl),
                        )
                    elif isinstance(attr, OffsetAttribute):
                        offset = attr.offset
                        if offset < current_offset:
                            raise ValueError("Offset must be greater than the current size.")
                        current_offset = offset
                    else:
                        raise TypeError("Only Field and OffsetAttribute are allowed in attributes.")

                # If we don't have a Field, we need to inflate the type as if we have no attributes
                if not resolved_type:
                    resolved_type = inflater.inflater_for(annotation, owner=(self, reference_type._type_impl))
            else:
                resolved_type = inflater.inflater_for(annotation, owner=(self, reference_type._type_impl))

            result = resolved_type(resolver.relative_from_own(current_offset, 0))
            setattr(self, name, result)
            self._members[name] = result
            current_offset += size_of(result)

    @classmethod
    def compute_own_size(cls: type[struct_impl], reference_type: type) -> None:
        """Compute the size of the struct."""
        size = 0

        for name, annotation, reference in iterate_annotation_chain(reference_type, terminate_at=struct):
            if name in reference.__dict__:
                # Field associated with the annotation
                attrs = getattr(reference, name)

                # If attrs is not a tuple, we need to convert it to a tuple
                if not isinstance(attrs, tuple):
                    attrs = (attrs,)

                # Assert that in all attributes, there is only one Field
                if sum(isinstance(attr, Field) for attr in attrs) > 1:
                    raise ValueError("Only one Field is allowed per attribute.")

                attribute = None

                for attr in attrs:
                    if isinstance(attr, Field):
                        attribute = cls._inflater.inflater_for((attr, annotation))(None)
                    elif isinstance(attr, OffsetAttribute):
                        offset = attr.offset
                        if offset < size:
                            raise ValueError("Offset must be greater than the current size.")
                        size = offset
                    else:
                        raise TypeError("Only Field and OffsetAttribute are allowed in attributes.")

                # If we don't have a Field, we need to inflate the attribute as if we have no attributes
                if not attribute:
                    attribute = cls._inflater.inflater_for(annotation)
            elif isinstance(annotation, Field):
                attribute = cls._inflater.inflater_for((annotation, annotation.base_type))(None)
            else:
                attribute = cls._inflater.inflater_for(annotation)

            size += size_of(attribute)

        cls.size = size

    def get(self: struct_impl) -> str:
        """Return the value of the struct."""
        return f"{self.name}(address={self.address}, size={size_of(self)})"

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
        members = ",\n".join(
            [f"{' ' * (indent + 4)}{name}: {member.to_str(indent + 4)}" for name, member in self._members.items()],
        )
        return f"""{self.name} {{
{members}
{" " * indent}}}"""

    def __repr__(self: struct_impl) -> str:
        """Return a string representation of the struct."""
        members = ",\n".join([f"{name}: {member}" for name, member in self._members.items()])
        return f"""{self.name} {{
    address: 0x{self.address:x},
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
