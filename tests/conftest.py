"""Fixtures: a FoxESS H3 on modbus-connection's in-memory mock backend."""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit

from foxess_modbus import FoxEssH3Inverter


def one_char_per_register(text: str, length: int) -> list[int]:
    """The H3 model encoding: one ASCII character in each register's low byte."""
    return [ord(c) for c in text.ljust(length, "\0")[:length]]


def s16(value: int) -> int:
    """A signed value as the register word the inverter sends."""
    return value & 0xFFFF


# Values read from an H3-10.0-E on Master 2.23 / Slave 1.03 / Manager 1.95
# (2026-09-10), where known; the rest are plausible.
H3_HOLDING: dict[int, int | list[int]] = {
    # -- identity --
    30000: one_char_per_register("   H3-10.0-E", 15),
    30016: [223, 103, 0x195],
    # -- PV --
    31000: [4520, 36, 1540],  # PV1 452.0 V, 3.6 A, 1.54 kW
    31003: [3100, 5, s16(-2)],  # PV2 310.0 V, 0.5 A, -0.002 kW (night noise)
    # -- grid --
    31006: [2301, 2299, 2305],
    31009: [45, 44, 46],
    31012: [1000, 1010, 990],  # 3.0 kW out
    31015: 5001,
    31022: [0, 0, 0],
    31025: 0,
    31026: [s16(-500), 200, 100],  # net -0.2 kW -> importing 0.2 kW
    31029: [800, 700, 600],
    # -- inverter --
    31032: [452, 301],  # 45.2 / 30.1 °C
    31041: 3,
    31044: [0x0001, 0, 0, 0, 0, 0, 0, 0],  # 31044..31051: Grid Lost Fault
    # -- battery --
    31034: [4103, s16(-18), s16(-730), 215, 93],  # charging 0.73 kW, SoC 93 %
    # -- BMS --
    31090: 99,
    31102: [250, 230],
    31123: 1234,  # 12.34 kWh
    31134: [3340, 3321],
    # -- energy: total 9820.5 kWh at 32003:32004, as on the real inverter --
    32000: [0, 50000, 123],
    32003: [1, 32669, 32670],  # 32005 = (98205 mod 65536) + 1 on manager >= 1.93
    32006: [1, 26432, 26433],
    32009: [0, 29931, 45],
    32012: [2, 37608, 12],
    32015: [0, 1000, 10],
    32018: [0, 2000, 20],
    32021: [4, 47298, 150],
    # -- settings --
    41000: 0,  # Self Use
    41007: [260, 250, 10, 100, 10],
}


def load(unit: MockModbusUnit, holding: dict[int, int | list[int]]) -> None:
    """Seed the mock's holding store."""
    unit.holding.update(holding)


@pytest.fixture
def h3(mock_modbus_unit: MockModbusUnit) -> FoxEssH3Inverter:
    """An H3-10.0-E on manager firmware 1.95."""
    load(mock_modbus_unit, H3_HOLDING)
    return FoxEssH3Inverter(mock_modbus_unit)
