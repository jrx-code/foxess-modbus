"""Model name and firmware versions, the 30000 register block."""

from __future__ import annotations

from ..fields import ModelStringField, VersionField
from ..model import FoxEssComponent


class Identity(FoxEssComponent):
    """What the inverter is and which firmware it runs. Read once at setup."""

    register_ranges = ((30000, 30018),)

    model = ModelStringField(30000, count=15)
    """Model name, e.g. ``H3-10.0-E``."""

    master_version = VersionField(30016, encoding="decimal")
    slave_version = VersionField(30017, encoding="decimal")
    manager_version = VersionField(30018, encoding="hex")
    """The ARM (manager) firmware. It decides which registers are valid."""
