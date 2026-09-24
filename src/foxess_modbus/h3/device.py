"""The top-level object for a FoxESS H3 hybrid inverter."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from modbus_connection.model import (
    ComponentGroup,
    Device,
    Raw,
    UpdateReport,
    read_optional,
)

from ..exceptions import UnsupportedModelError
from ..fields import FirmwareVersion
from ..models import InverterModel, identify
from .energy import Energy
from .identity import Identity
from .live import Battery, Bms, Grid, InverterState, PvStrings
from .settings import Settings

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

# From this manager firmware on, 32005/32008 no longer hold today's energy.
BATTERY_TODAY_BROKEN_FROM = FirmwareVersion(1, 93)

READINGS = ("live", "bms", "energy")
SETTINGS = ("settings",)


class FoxEssH3Inverter(Device):
    """A FoxESS H3 reached through a ``ModbusUnit``.

    The live components (``pv``, ``grid``, ``inverter``, ``battery``) are read
    together as ``live``; an ``UpdateReport`` names them by that.
    """

    def __init__(self, unit: ModbusUnit, *, timeout: float | None = None) -> None:
        """Set up the sub-systems. ``timeout`` raises the unit's reply timeout."""
        super().__init__(unit)
        unit.require_timeout(timeout)

        self.identity = Identity(unit)
        self.pv = PvStrings(unit)
        self.grid = Grid(unit)
        self.inverter = InverterState(unit)
        self.battery = Battery(unit)
        # The four share one block of 31000-31051, so they read as one.
        self.live = ComponentGroup(
            unit, [self.pv, self.grid, self.inverter, self.battery]
        )
        self.energy = Energy(unit)
        self.settings = Settings(unit)

        # Settled by setup: not every H3 answers the BMS block.
        self.bms: Bms | None = None
        self.model: InverterModel | None = None

    async def _async_setup(self) -> None:
        """Read identity, check the model, and settle what this firmware serves."""
        await self.identity.async_update(notify=False)
        model_name = self.identity.model or ""
        model = identify(model_name)
        if model is None or model.family != "H3":
            raise UnsupportedModelError(model_name)
        self.model = model

        manager = self.identity.manager_version
        self.energy.battery_today_valid = (
            manager is None or manager < BATTERY_TODAY_BROKEN_FROM
        )
        self.bms = await read_optional(Bms(self.modbus_unit))

    @property
    def serial_number(self) -> str | None:
        """The H3 does not report its serial number over Modbus."""
        return None

    async def async_update_readings(self) -> UpdateReport:
        """Refresh what the inverter measures."""
        return await self.async_poll(READINGS)

    async def async_update_settings(self) -> UpdateReport:
        """Refresh what the inverter has been configured to do."""
        return await self.async_poll(SETTINGS)

    async def async_update(self) -> UpdateReport:
        """Refresh readings and settings in one report."""
        return await self.async_poll((*READINGS, *SETTINGS))

    async def async_read_raw(self, names: Iterable[str] | None = None) -> Raw:
        """Every register this inverter reads, undecoded, for diagnostics."""
        if names is None:
            names = ("identity", *READINGS, *SETTINGS)
        return await super().async_read_raw(names)
