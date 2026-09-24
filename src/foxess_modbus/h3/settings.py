"""Work mode and battery limits, the 41000 register block.

41001-41006 (charge periods) answer illegal address on the H3, so 41000 and
41007-41011 are read as two blocks. Every write is a single FC06: manager
firmware 1.93 and later refuses FC16 on these registers.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum

from modbus_connection.model import enum, gauge, integer

from ..model import FoxEssComponent


class WorkMode(IntEnum):
    """The inverter's energy management mode."""

    SELF_USE = 0
    FEED_IN_FIRST = 1
    BACK_UP = 2
    PEAK_SHAVING = 4


def _work_mode(value: int) -> WorkMode:
    return WorkMode(value)


def _between[T: (int, float)](low: T, high: T) -> Callable[[T], T]:
    def validate(value: T) -> T:
        if not low <= value <= high:
            raise ValueError(f"{value} is outside {low}-{high}")
        return value

    return validate


class Settings(FoxEssComponent):
    """What the inverter has been configured to do."""

    register_ranges = ((41000, 41000), (41007, 41011))

    work_mode = enum(41000, WorkMode, writable=_work_mode)
    max_charge_current = gauge(
        41007, 0.1, signed=False, unit="A", writable=_between(0.0, 50.0)
    )
    max_discharge_current = gauge(
        41008, 0.1, signed=False, unit="A", writable=_between(0.0, 50.0)
    )
    min_soc = integer(41009, signed=False, unit="%", writable=_between(10, 100))
    """Lowest state of charge off grid."""
    max_soc = integer(41010, signed=False, unit="%", writable=_between(10, 100))
    min_soc_on_grid = integer(41011, signed=False, unit="%", writable=_between(10, 100))
    """Lowest state of charge while the grid is up."""
