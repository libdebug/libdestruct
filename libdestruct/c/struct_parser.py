#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import ctypes
import re
import subprocess
import tempfile
from typing import TYPE_CHECKING

from pycparser import c_ast, c_parser

from libdestruct.common.array.array_of import array_of
from libdestruct.common.ptr.ptr_factory import ptr_to, ptr_to_self
from libdestruct.common.struct import struct

if TYPE_CHECKING:
    from libdestruct.common.obj import obj


PARSED_STRUCTS = {}
"""A cache for parsed struct definitions, indexed by name."""

TYPEDEFS = {}
"""A cache for parsed type definitions, indexed by name."""


def definition_to_type(definition: str) -> type[obj]:
    """Converts a C struct definition to a struct object."""
    parser = c_parser.CParser()

    # If the definition contains includes, we must expand them.
    if "#include" in definition:
        definition = cleanup_attributes(expand_includes(definition))

    try:
        ast = parser.parse(definition)
    except c_parser.ParseError as e:
        raise ValueError(
            "Invalid definition. Please add the necessary includes if using non-standard type definitions."
        ) from e

    # We assume that the root declaration is the last one.
    root = ast.ext[-1].type

    if not isinstance(root, c_ast.Struct):
        raise TypeError("Definition must be a struct.")

    # We parse each declaration in the definition, except the last one, if it is a struct.
    for decl in ast.ext[:-1]:
        if isinstance(decl.type, c_ast.Struct):
            struct_node = decl.type

            if struct_node.name:
                PARSED_STRUCTS[struct_node.name] = struct_to_type(struct_node)
        elif isinstance(decl, c_ast.Typedef):
            name, definition = typedef_to_pair(decl)
            TYPEDEFS[name] = definition

    result = struct_to_type(root)

    PARSED_STRUCTS[root.name] = result

    return result


def struct_to_type(struct_node: c_ast.Struct) -> type[struct]:
    """Converts a C struct to a struct object."""
    if not isinstance(struct_node, c_ast.Struct):
        raise TypeError("Definition must be a struct.")

    fields = {}

    if not struct_node.decls and struct_node.name in PARSED_STRUCTS:
        # We can check if the struct is already parsed.
        return PARSED_STRUCTS[struct_node.name]
    elif not struct_node.decls:
        raise ValueError("Struct must have fields.")

    for decl in struct_node.decls:
        name = decl.name
        typ = type_decl_to_type(decl.type, struct_node)
        fields[name] = typ

    type_name = struct_node.name if struct_node.name else "anon_struct"

    return type(type_name, (struct,), {"__annotations__": fields})


def ptr_to_type(ptr: c_ast.PtrDecl, parent: c_ast.Struct | None = None) -> type[obj]:
    """Converts a C pointer to a type."""
    if not isinstance(ptr, c_ast.PtrDecl):
        raise TypeError("Definition must be a pointer.")

    # Handle nested pointers (e.g., int **pp) by recursively wrapping in ptr_to
    if isinstance(ptr.type, c_ast.PtrDecl):
        inner = ptr_to_type(ptr.type, parent)
        return ptr_to(inner)

    if not isinstance(ptr.type, c_ast.TypeDecl):
        raise TypeError("Definition must be a type declaration.")

    # Special case: this is a pointer to self
    # Note that ptr can either be a struct or an identifier.
    ptr_name = ptr.type.type.name if isinstance(ptr.type.type, c_ast.Struct) else ptr.type.type.names[0]
    if parent and ptr_name == parent.name:
        return ptr_to_self()

    typ = type_decl_to_type(ptr.type)

    return ptr_to(typ)


def arr_to_type(arr: c_ast.ArrayDecl) -> type[obj]:
    """Converts a C array to a type."""
    if not isinstance(arr, c_ast.ArrayDecl):
        raise TypeError("Definition must be an array.")

    if not isinstance(arr.type, c_ast.TypeDecl) and not isinstance(arr.type, c_ast.PtrDecl):
        raise TypeError("Definition must be a type declaration.")

    typ = ptr_to_type(arr.type) if isinstance(arr.type, c_ast.PtrDecl) else type_decl_to_type(arr.type)

    return array_of(typ, int(arr.dim.value))


def type_decl_to_type(decl: c_ast.TypeDecl, parent: c_ast.Struct | None = None) -> type[obj]:
    """Converts a C type declaration to a type."""
    if (
        not isinstance(decl, c_ast.TypeDecl)
        and not isinstance(decl, c_ast.PtrDecl)
        and not isinstance(decl, c_ast.ArrayDecl)
    ):
        raise TypeError("Definition must be a type declaration.")

    if isinstance(decl, c_ast.PtrDecl):
        return ptr_to_type(decl, parent)

    if isinstance(decl, c_ast.ArrayDecl):
        return arr_to_type(decl)

    if isinstance(decl.type, c_ast.Struct):
        return struct_to_type(decl.type)

    if isinstance(decl.type, c_ast.IdentifierType):
        return identifier_to_type(decl.type)

    raise TypeError("Unsupported type.")


def typedef_to_pair(typedef: c_ast.Typedef) -> tuple[str, type[obj]]:
    """Converts a C typedef to a pair of name and definition."""
    if not isinstance(typedef, c_ast.Typedef):
        raise TypeError("Definition must be a typedef.")

    if not isinstance(typedef.type, c_ast.TypeDecl):
        raise TypeError("Definition must be a type declaration.")

    name = "".join(typedef.name)
    definition = type_decl_to_type(typedef.type)

    return name, definition


def to_uniform_name(name: str) -> str:
    """Converts a name to a uniform name."""
    name = name.replace("unsigned", "u")
    name = name.replace("_Bool", "bool")
    name = name.replace("uchar", "ubyte")  # uchar is not a valid ctypes type

    # We have to convert each intX, uintX, intX_t, uintX_t to the original char, short etc.
    name = name.replace("uint8_t", "ubyte")
    name = name.replace("int8_t", "char")
    name = name.replace("int16_t", "short")
    name = name.replace("int32_t", "int")
    name = name.replace("int64_t", "longlong")

    # We have to convert uintptr_t
    name = name.replace("uintptr_t", "ulonglong")

    # Only size_t, ssize_t and time_t can end with _t
    if not any(x in name for x in ["size", "ssize", "time"]):
        name = name.replace("_t", "")

    return name


def expand_includes(definition: str) -> str:
    """Expands includes in a C definition using the C preprocessor."""
    # TODO: cache this result between subsequent runs of the same script
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c") as f:
        f.write(definition)
        f.flush()

        result = subprocess.run(["cc", "-std=c99", "-E", f.name], capture_output=True, text=True, check=True)  # noqa: S607

    return result.stdout


def cleanup_attributes(definition: str) -> str:
    """Cleans up attributes in a C definition."""
    # Remove __attribute__ ((...)) from the definition.
    pattern = r"__attribute__\s*\(\((?:[^()]+|\((?:[^()]+|\([^()]*\))*\))*\)\)"  # ChatGPT provided this, don't ask me
    return re.sub(pattern, "", definition)


def identifier_to_type(identifier: c_ast.IdentifierType) -> type[obj]:
    """Converts a C identifier to a type."""
    if not isinstance(identifier, c_ast.IdentifierType):
        raise TypeError("Definition must be an identifier.")

    identifier_name = "".join(identifier.names)

    ctypes_name = "c_" + identifier_name

    if hasattr(ctypes, ctypes_name):
        return getattr(ctypes, ctypes_name)

    # Convert the identifier name to a uniform name, e.g., "unsigned int" -> "uint".
    ctypes_name = "c_" + to_uniform_name(identifier_name)

    if hasattr(ctypes, ctypes_name):
        return getattr(ctypes, ctypes_name)

    # Check if we have a typedef to resolve this
    if identifier_name in TYPEDEFS:
        return TYPEDEFS[identifier_name]

    raise ValueError(f"Unsupported identifier: {identifier_name}.")
