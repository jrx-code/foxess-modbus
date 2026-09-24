"""The H3 register map, decoded over the mock backend."""

from __future__ import annotations

import pytest
from modbus_connection import IllegalDataAddressError, IllegalDataValueError
from modbus_connection.mock import MockModbusUnit, WriteEvent

from foxess_modbus import (
    FirmwareVersion,
    FoxEssH3Inverter,
    UnsupportedModelError,
    WorkMode,
)

from .conftest import H3_HOLDING, load, one_char_per_register


async def test_setup_reads_identity(h3: FoxEssH3Inverter) -> None:
    await h3.async_ensure_setup()
    assert h3.identity.model == "H3-10.0-E"
    assert h3.model is not None
    assert h3.model.family == "H3"
    assert h3.model.rated_power == 10.0
    assert str(h3.identity.master_version) == "2.23"
    assert str(h3.identity.slave_version) == "1.03"
    assert h3.identity.manager_version == FirmwareVersion(1, 95)
    assert h3.serial_number is None


async def test_readings_decode(h3: FoxEssH3Inverter) -> None:
    report = await h3.async_update_readings()
    assert report.updated == {"live", "bms", "energy"}
    assert report.complete

    assert h3.pv.pv1_voltage == 452.0
    assert h3.pv.pv1_power == 1.54
    assert h3.pv.pv2_power == -0.002
    assert h3.pv.pv_power == 1.54  # night noise on PV2 counts as 0

    assert h3.grid.grid_frequency == 50.01
    assert h3.grid.inverter_power == 3.0
    assert h3.grid.ct_power == -0.2
    assert h3.grid.feed_in_power == 0.0
    assert h3.grid.grid_import_power == 0.2
    assert h3.grid.load_power == 2.1

    assert h3.inverter.inverter_temperature == 45.2
    assert h3.inverter.state_code == 3
    assert h3.inverter.active_faults == ["Grid Lost Fault"]

    assert h3.battery.battery_soc == 93
    assert h3.battery.battery_power == -0.73
    assert h3.battery.battery_charge_power == 0.73
    assert h3.battery.battery_discharge_power == 0.0

    assert h3.bms is not None
    assert h3.bms.battery_soh == 99
    assert h3.bms.energy_remaining == 12.34
    assert h3.bms.cell_voltage_low == 3321

    assert h3.energy.battery_charge_total == 9820.5
    assert h3.energy.solar_total == 5000.0
    assert h3.energy.solar_today == 12.3


async def test_battery_today_hidden_on_manager_193(h3: FoxEssH3Inverter) -> None:
    """Manager 1.93+ writes (total mod 65536) + 1 where today's energy was."""
    await h3.async_update_readings()
    assert h3.energy.battery_today_valid is False
    assert h3.energy.battery_charge_today is None
    assert h3.energy.battery_discharge_today is None


async def test_battery_today_kept_before_manager_193(
    mock_modbus_unit: MockModbusUnit,
) -> None:
    load(mock_modbus_unit, H3_HOLDING)
    mock_modbus_unit.holding[30018] = 0x192
    mock_modbus_unit.holding[32005] = 190
    h3 = FoxEssH3Inverter(mock_modbus_unit)
    await h3.async_update_readings()
    assert h3.energy.battery_charge_today == 19.0


async def test_readings_cost_three_block_reads(
    h3: FoxEssH3Inverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await h3.async_ensure_setup()
    mock_modbus_unit.read_events.clear()
    await h3.async_update_readings()
    blocks = [(b.address, b.count) for b in mock_modbus_unit.read_events]
    assert blocks == [(31000, 52), (31090, 46), (32000, 24)]


async def test_settings_skip_the_charge_periods(
    h3: FoxEssH3Inverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """41001-41006 answer illegal address on the H3; no read may span them."""
    for address in range(41001, 41007):
        mock_modbus_unit.fail_read(address, IllegalDataAddressError())
    await h3.async_ensure_setup()
    mock_modbus_unit.read_events.clear()

    report = await h3.async_update_settings()

    assert report.updated == {"settings"}
    blocks = [(b.address, b.count) for b in mock_modbus_unit.read_events]
    assert blocks == [(41000, 1), (41007, 5)]
    assert h3.settings.work_mode is WorkMode.SELF_USE
    assert h3.settings.max_charge_current == 26.0
    assert h3.settings.min_soc == 10
    assert h3.settings.max_soc == 100
    assert h3.settings.min_soc_on_grid == 10


async def test_bms_is_optional(mock_modbus_unit: MockModbusUnit) -> None:
    load(mock_modbus_unit, H3_HOLDING)
    mock_modbus_unit.fail_read(31090, IllegalDataAddressError())
    h3 = FoxEssH3Inverter(mock_modbus_unit)
    report = await h3.async_update_readings()
    assert h3.bms is None
    assert report.updated == {"live", "energy"}


async def test_unsupported_model(mock_modbus_unit: MockModbusUnit) -> None:
    load(mock_modbus_unit, H3_HOLDING)
    mock_modbus_unit.holding[30000] = one_char_per_register("H1-5.0-E", 15)
    h3 = FoxEssH3Inverter(mock_modbus_unit)
    with pytest.raises(UnsupportedModelError, match="H1-5.0-E"):
        await h3.async_update()


async def test_writes_are_single_register(
    h3: FoxEssH3Inverter, mock_modbus_unit: MockModbusUnit
) -> None:
    events: list[WriteEvent] = []
    mock_modbus_unit.on_write(events.append)

    await h3.settings.write("min_soc_on_grid", 11)
    await h3.settings.write("work_mode", WorkMode.FEED_IN_FIRST)
    await h3.settings.write("max_charge_current", 20.5)

    assert [(e.address, e.values, e.function_code) for e in events] == [
        (41011, [11], 0x06),
        (41000, [1], 0x06),
        (41007, [205], 0x06),
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [("min_soc", 9), ("max_soc", 101), ("max_charge_current", 50.1), ("work_mode", 3)],
)
async def test_writes_out_of_range_are_refused(
    h3: FoxEssH3Inverter, field: str, value: float
) -> None:
    with pytest.raises(ValueError):
        await h3.settings.write(field, value)


async def test_device_rejecting_a_write_raises(
    h3: FoxEssH3Inverter, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.fail_write(41011, IllegalDataValueError())
    with pytest.raises(IllegalDataValueError):
        await h3.settings.write("min_soc_on_grid", 20)


async def test_read_raw_covers_every_block(h3: FoxEssH3Inverter) -> None:
    raw = await h3.async_read_raw()
    holding = raw["holding"]
    assert holding[30016] == 223
    assert holding[31038] == 93
    assert holding[32004] == 32669
    assert holding[41011] == 10
    assert 41001 not in holding
