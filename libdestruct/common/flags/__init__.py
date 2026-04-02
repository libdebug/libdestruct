#
# This file is part of libdestruct (https://github.com/mrindeciso/libdestruct).
# Copyright (c) 2026 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from libdestruct.common.flags.flags import flags
from libdestruct.common.flags.flags_of import flags_of

__all__ = ["flags", "flags_of"]

import libdestruct.common.flags.flags_field_inflater  # noqa: F401
