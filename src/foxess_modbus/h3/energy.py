"""Energy counters, the 32000 register block. All in kWh."""

from __future__ import annotations

from modbus_connection.model import gauge, uint32

from ..model import FoxEssComponent


class Energy(FoxEssComponent):
    """Lifetime and daily energy counters."""

    solar_total = uint32(32000, scale=0.1, unit="kWh")
    solar_today = gauge(32002, 0.1, signed=False, unit="kWh")
    battery_charge_total = uint32(32003, scale=0.1, unit="kWh")
    _battery_charge_today = gauge(32005, 0.1, signed=False, unit="kWh")
    battery_discharge_total = uint32(32006, scale=0.1, unit="kWh")
    _battery_discharge_today = gauge(32008, 0.1, signed=False, unit="kWh")
    feed_in_total = uint32(32009, scale=0.1, unit="kWh")
    feed_in_today = gauge(32011, 0.1, signed=False, unit="kWh")
    grid_import_total = uint32(32012, scale=0.1, unit="kWh")
    grid_import_today = gauge(32014, 0.1, signed=False, unit="kWh")
    yield_total = uint32(32015, scale=0.1, unit="kWh")
    yield_today = gauge(32017, 0.1, signed=False, unit="kWh")
    input_total = uint32(32018, scale=0.1, unit="kWh")
    input_today = gauge(32020, 0.1, signed=False, unit="kWh")
    load_total = uint32(32021, scale=0.1, unit="kWh")
    load_today = gauge(32023, 0.1, signed=False, unit="kWh")

    battery_today_valid: bool = True
    """Whether 32005 and 32008 hold today's battery energy.

    Manager firmware 1.93 and later writes ``(total mod 65536) + 1`` there
    instead. The registers still answer, so they stay in the block read.
    """

    @property
    def battery_charge_today(self) -> float | None:
        """Energy into the battery today; ``None`` where the firmware lacks it."""
        return self._battery_charge_today if self.battery_today_valid else None

    @property
    def battery_discharge_today(self) -> float | None:
        """Energy out of the battery today; ``None`` where the firmware lacks it."""
        return self._battery_discharge_today if self.battery_today_valid else None
