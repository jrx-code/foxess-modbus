"""Live measurements, the 31000 register block.

Power is in kW. Signs follow the inverter: grid CT power is positive while
exporting, battery power is positive while discharging.
"""

from __future__ import annotations

from modbus_connection.model import gauge, integer, raw_register

from ..model import FoxEssComponent
from .faults import active_faults


def _sum(*values: float | None) -> float | None:
    """The sum of three phase values, or ``None`` if any is missing."""
    if any(value is None for value in values):
        return None
    return round(sum(v for v in values if v is not None), 3)


class PvStrings(FoxEssComponent):
    """The two MPPT inputs."""

    pv1_voltage = gauge(31000, 0.1, unit="V")
    pv1_current = gauge(31001, 0.1, unit="A")
    pv1_power = gauge(31002, 0.001, unit="kW")
    pv2_voltage = gauge(31003, 0.1, unit="V")
    pv2_current = gauge(31004, 0.1, unit="A")
    pv2_power = gauge(31005, 0.001, unit="kW")

    @property
    def pv_power(self) -> float | None:
        """Both strings together; a small negative reading at night counts as 0."""
        if self.pv1_power is None or self.pv2_power is None:
            return None
        return round(max(self.pv1_power, 0) + max(self.pv2_power, 0), 3)


class Grid(FoxEssComponent):
    """Grid, inverter output, EPS, CT and load, per phase."""

    grid_voltage_r = gauge(31006, 0.1, signed=False, unit="V")
    grid_voltage_s = gauge(31007, 0.1, signed=False, unit="V")
    grid_voltage_t = gauge(31008, 0.1, signed=False, unit="V")
    inverter_current_r = gauge(31009, 0.1, unit="A")
    inverter_current_s = gauge(31010, 0.1, unit="A")
    inverter_current_t = gauge(31011, 0.1, unit="A")
    inverter_power_r = gauge(31012, 0.001, unit="kW")
    inverter_power_s = gauge(31013, 0.001, unit="kW")
    inverter_power_t = gauge(31014, 0.001, unit="kW")
    grid_frequency = gauge(31015, 0.01, signed=False, unit="Hz")
    eps_power_r = gauge(31022, 0.001, unit="kW")
    eps_power_s = gauge(31023, 0.001, unit="kW")
    eps_power_t = gauge(31024, 0.001, unit="kW")
    eps_frequency = gauge(31025, 0.01, signed=False, unit="Hz")
    ct_power_r = gauge(31026, 0.001, unit="kW")
    """Grid CT, phase R. Positive while exporting."""
    ct_power_s = gauge(31027, 0.001, unit="kW")
    ct_power_t = gauge(31028, 0.001, unit="kW")
    load_power_r = gauge(31029, 0.001, unit="kW")
    load_power_s = gauge(31030, 0.001, unit="kW")
    load_power_t = gauge(31031, 0.001, unit="kW")

    @property
    def inverter_power(self) -> float | None:
        """Inverter output over all phases."""
        return _sum(self.inverter_power_r, self.inverter_power_s, self.inverter_power_t)

    @property
    def eps_power(self) -> float | None:
        """EPS output over all phases."""
        return _sum(self.eps_power_r, self.eps_power_s, self.eps_power_t)

    @property
    def ct_power(self) -> float | None:
        """Grid CT over all phases. Positive while exporting."""
        return _sum(self.ct_power_r, self.ct_power_s, self.ct_power_t)

    @property
    def load_power(self) -> float | None:
        """House load over all phases."""
        return _sum(self.load_power_r, self.load_power_s, self.load_power_t)

    @property
    def feed_in_power(self) -> float | None:
        """Power exported to the grid, 0 while importing."""
        ct = self.ct_power
        return None if ct is None else max(ct, 0.0)

    @property
    def grid_import_power(self) -> float | None:
        """Power imported from the grid, 0 while exporting."""
        ct = self.ct_power
        return None if ct is None else max(-ct, 0.0)


class InverterState(FoxEssComponent):
    """Temperatures, state code and fault words."""

    inverter_temperature = gauge(31032, 0.1, unit="°C")
    ambient_temperature = gauge(31033, 0.1, unit="°C")
    state_code = integer(31041)
    """Raw run state. FoxESS publishes no table for the H3."""

    fault_1 = raw_register(31044)
    fault_2 = raw_register(31045)
    fault_3 = raw_register(31047)
    fault_4 = raw_register(31048)
    fault_5 = raw_register(31049)
    fault_6 = raw_register(31050)
    fault_7 = raw_register(31051)

    @property
    def active_faults(self) -> list[str] | None:
        """The names of the faults the inverter reports now."""
        words = (
            self.fault_1,
            self.fault_2,
            self.fault_3,
            self.fault_4,
            self.fault_5,
            self.fault_6,
            self.fault_7,
        )
        if any(word is None for word in words):
            return None
        return active_faults([w for w in words if w is not None])


class Battery(FoxEssComponent):
    """The battery as the inverter sees it."""

    battery_voltage = gauge(31034, 0.1, unit="V")
    battery_current = gauge(31035, 0.1, unit="A")
    battery_power = gauge(31036, 0.001, unit="kW")
    """Positive while discharging."""
    battery_temperature = gauge(31037, 0.1, unit="°C")
    battery_soc = integer(31038, signed=False, unit="%")

    @property
    def battery_charge_power(self) -> float | None:
        """Charging power, 0 while discharging."""
        power = self.battery_power
        return None if power is None else max(-power, 0.0)

    @property
    def battery_discharge_power(self) -> float | None:
        """Discharging power, 0 while charging."""
        power = self.battery_power
        return None if power is None else max(power, 0.0)


class Bms(FoxEssComponent):
    """What the battery management system reports. Not every H3 serves it."""

    # The whole block answers, so one read covers the gap 31104-31122.
    register_ranges = ((31090, 31135),)

    battery_soh = integer(31090, signed=False, unit="%")
    cell_temperature_high = gauge(31102, 0.1, unit="°C")
    cell_temperature_low = gauge(31103, 0.1, unit="°C")
    energy_remaining = gauge(31123, 0.01, signed=False, unit="kWh")
    cell_voltage_high = integer(31134, signed=False, unit="mV")
    cell_voltage_low = integer(31135, signed=False, unit="mV")
