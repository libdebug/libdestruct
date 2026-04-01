#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING, get_args, get_origin

from libdestruct.common.field import Field

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from typing_extensions import Self

    from libdestruct.backing.resolver import Resolver
    from libdestruct.common.obj import obj


class TypeRegistry:
    """A registry for object types."""

    mapping: dict[type[obj], type[obj]]
    """The mapping of object types to their implementations."""

    type_handlers: dict[type, list[Callable[[type[obj]], type[obj] | None]]]
    """The handlers for generic object types, with basic inheritance support."""

    generic_handlers: dict[type, list[Callable]]
    """The handlers for subscripted generic types like ptr[T]."""

    instance_handlers: dict[
        type,
        list[
            Callable[
                [object, type[obj], tuple[obj, type[obj]] | None],
                Callable[[Resolver], obj] | None,
            ]
        ],
    ]
    """The handlers for specific object instances, such as fields."""

    def __new__(cls: type[TypeRegistry]) -> Self:
        """Create a new instance of the type registry."""
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)

            cls._instance.mapping = {}
            cls._instance.type_handlers = {}
            cls._instance.generic_handlers = {}
            cls._instance.instance_handlers = {}

        return cls._instance

    def inflater_for(
        self: TypeRegistry,
        item: type[obj] | Field | tuple[object, type[obj]],
        owner: tuple[obj, type[obj]] | None = None,
    ) -> type[obj]:
        """Return the inflater for the given object type.

        Args:
            item: The object type.
            owner: The owner of the object type.

        Returns:
            The inflater for the object type.
        """
        origin = get_origin(item)
        if origin is not None:
            return self._inflater_for_generic(item, origin, get_args(item), owner)

        if isinstance(item, type):
            if item in self.mapping:
                return self.mapping[item]

            return self._inflater_for_type(item)

        return self._inflater_for_instance(item, owner)

    def _inflater_for_type(self: TypeRegistry, item: type[obj]) -> type[obj]:
        parent = item.__base__

        while parent:
            for handler in self.type_handlers.get(parent, []):
                result = handler(item)

                if result is not None:
                    self.mapping[item] = result
                    return result
            parent = parent.__base__

        raise ValueError(f"No applicable inflater found for {item}")

    def _inflater_for_generic(
        self: TypeRegistry,
        item: object,
        origin: type,
        args: tuple,
        owner: tuple[obj, type[obj]] | None,
    ) -> Callable[[Resolver], obj]:
        for handler in self.generic_handlers.get(origin, []):
            result = handler(item, args, owner)
            if result is not None:
                return result

        raise ValueError(f"No applicable inflater found for subscripted type {item}")

    def _inflater_for_instance(
        self: TypeRegistry,
        instance: Field | tuple[object, type[obj]],
        owner: tuple[obj, type[obj]] | None,
    ) -> Callable[[Resolver], obj]:
        # Check if instance is already the bound method of an inflater. If so, just return it, as we resolved it already
        if callable(instance) and hasattr(instance, "__self__") and isinstance(instance.__self__, Field):
            return instance

        if isinstance(instance, tuple):
            item, annotation = instance
        else:
            item, annotation = instance, None

        base = item.__class__

        for handler in self.instance_handlers.get(base, []):
            result = handler(item, annotation, owner)

            if result is not None:
                return result

        raise ValueError(f"No applicable inflater found for {item}")

    def register_type_handler(
        self: TypeRegistry,
        parent: type[obj],
        handler: Callable[[type[obj]], type[obj] | None],
    ) -> None:
        """Register a handler for a type.

        Args:
            parent: The parent type.
            handler: The handler for the type.
        """
        if parent not in self.type_handlers:
            self.type_handlers[parent] = []

        if handler not in self.type_handlers[parent]:
            self.type_handlers[parent].append(handler)

    def register_instance_handler(
        self: TypeRegistry,
        parent: type,
        handler: Callable[
            [object, type[obj], tuple[obj, type[obj]] | None],
            Callable[[Resolver], obj] | None,
        ],
    ) -> None:
        """Register a handler for an instance.

        Args:
            parent: The parent type.
            handler: The handler for the instance.
        """
        if parent not in self.instance_handlers:
            self.instance_handlers[parent] = []

        if handler not in self.instance_handlers[parent]:
            self.instance_handlers[parent].append(handler)

    def register_generic_handler(
        self: TypeRegistry,
        origin: type,
        handler: Callable,
    ) -> None:
        """Register a handler for a subscripted generic type.

        Args:
            origin: The origin type (e.g., ptr for ptr[T]).
            handler: The handler for the subscripted type.
        """
        if origin not in self.generic_handlers:
            self.generic_handlers[origin] = []

        if handler not in self.generic_handlers[origin]:
            self.generic_handlers[origin].append(handler)

    def register_mapping(
        self: TypeRegistry,
        parent: type[obj],
        implementation: type[obj],
    ) -> None:
        """Register an implementation for a type.

        Args:
            parent: The parent type.
            implementation: The implementation for the type.
        """
        self.mapping[parent] = implementation
