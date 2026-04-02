#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from libdestruct.common.array.array import array
from libdestruct.common.array.array_of import array_of
from libdestruct.common.array.vla_of import vla_of

__all__ = ["array", "array_of", "vla_of"]

import libdestruct.common.array.array_field_inflater
import libdestruct.common.array.vla_field_inflater  # noqa: F401 — side-effect: registers VLA handler
