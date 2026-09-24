"""The component base every FoxESS sub-system builds on."""

from __future__ import annotations

from modbus_connection.model import Component

__all__ = ["FoxEssComponent"]


class FoxEssComponent(Component):
    """A sub-system of a FoxESS inverter.

    Everything sits in holding registers. RS485 gateways and the inverter
    itself answer block reads of up to 100 registers.
    """

    max_span = 100
