# foxess-modbus

Read and control FoxESS hybrid inverters over Modbus, as typed Python objects.

The library is built on
[modbus-connection](https://home-assistant-libs.github.io/modbus-connection/).
It takes a `ModbusUnit` and never opens a connection itself. The caller owns
the link. This keeps the library backend-neutral: it runs over tmodbus,
pymodbus, or the in-memory mock unchanged.

It backs the `fox_ess` Home Assistant integration. It has no Home Assistant
dependency.

## Supported inverters

| Family | Connection | Status |
|---|---|---|
| H3 (`H3-x.x-E`) | RS485 (AUX port) through a Modbus TCP gateway | supported |
| H3-Smart, H3 Pro, H1, KH, AC1/AC3 | - | recognised by `identify()`, not read yet |

## Example

```python
import asyncio

from modbus_connection import ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from foxess_modbus import FoxEssH3Inverter, WorkMode


async def main() -> None:
    connection = ModbusConnection(ModbusTcpParams(host="192.168.1.50", port=502))
    try:
        inverter = FoxEssH3Inverter(connection.for_unit(247))
        await inverter.async_update()

        print(inverter.model, inverter.identity.manager_version)
        print("PV", inverter.pv.pv_power, "kW")
        print("SoC", inverter.battery.battery_soc, "%")
        print("Grid", inverter.grid.ct_power, "kW (positive = export)")

        await inverter.settings.write("work_mode", WorkMode.SELF_USE)
    finally:
        await connection.close()


asyncio.run(main())
```

## The device object

`FoxEssH3Inverter` is a `modbus_connection.model.Device`. Its sub-systems are
`Component`s:

| Attribute | Registers | Polled by |
|---|---|---|
| `identity` | 30000-30018 | setup only |
| `live` (`pv`, `grid`, `inverter`, `battery`) | 31000-31051, one block read | `async_update_readings()` |
| `bms` (optional) | 31090-31135 | `async_update_readings()` |
| `energy` | 32000-32023 | `async_update_readings()` |
| `settings` | 41000, 41007-41011 | `async_update_settings()` |

Each update method returns an `UpdateReport`. A sub-system the inverter
refuses lands in `report.failed`, and the rest still refresh.

Signs follow the inverter. Grid CT power is positive while exporting. Battery
power is positive while discharging. The `feed_in_power`,
`grid_import_power`, `battery_charge_power` and `battery_discharge_power`
properties split them into non-negative values.

## Firmware notes

- Manager firmware 1.93 and later answers illegal address for the charge
  periods at 41001-41006. No read spans them.
- Manager firmware 1.93 and later writes `(total mod 65536) + 1` into 32005
  and 32008 instead of today's battery energy. `battery_charge_today` and
  `battery_discharge_today` read `None` there.
- Manager firmware 1.93 and later accepts only single-register writes (FC06)
  on the settings. Every write in this library is a single FC06.
- Master 2.23 / Manager 1.95 sends most RS485 replies without the slave
  address byte. A Modbus TCP gateway forwards such a reply as a frame with
  the wrong unit id, and a strict client rejects it. This needs a fix in the
  Modbus client, not in this library.

## Develop

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy
```

The tests run against the modbus-connection mock backend. They need no
inverter.
