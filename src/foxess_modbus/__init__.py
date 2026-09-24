"""Read and control FoxESS hybrid inverters over Modbus, as typed Python objects."""

from modbus_connection.model import UpdateReport

from .exceptions import FoxEssError, UnsupportedModelError
from .fields import FirmwareVersion
from .h3 import FoxEssH3Inverter, WorkMode
from .models import InverterModel, identify

__all__ = [
    "FirmwareVersion",
    "FoxEssError",
    "FoxEssH3Inverter",
    "InverterModel",
    "UnsupportedModelError",
    "UpdateReport",
    "WorkMode",
    "identify",
]
