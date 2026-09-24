# foxess-modbus (library)

Device library for FoxESS inverters on
[modbus-connection](https://home-assistant-libs.github.io/modbus-connection/),
following the "device object" pattern from the HA Modbus guide
(https://developers.home-assistant.io/docs/modbus/introduction). Consumed by the
`fox_ess` integration in `../hassio-integration-fox-ess`. Started 2026-09-24 from
scratch; the fork `../hassio-integration-foxess-modbus` is reference material only
(register map, firmware findings in its `docs/ANALYSIS-2026-09-10-fw223.md`).

Chat in Polish, code/commits/docs in English (Simplified Technical English, like
modbus-connection's docs).

## Rules

- No Home Assistant import. Take a `ModbusUnit`, never open a connection.
- One `Component` per sub-system, one file per register block. Metadata (unit,
  validators) lives on the field.
- Test against the mock (`mock_modbus_unit` fixture), assert block reads with
  `read_events` whenever a change touches the read plan.
- Writes: single FC06 only (manager fw >= 1.93 refuses FC16 on 41xxx/44xxx).
- `modbus-connection>=4.12.1` (needs `Device`). HA 2026.9.x pins 4.10.0, HA dev /
  2026.10 pins 4.12.1.

## Dev

`uv sync && uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy`
(no system uv here: scratch venv uv, or `.venv/bin/...` directly).

## Scope

H3 only (our H3-10.0-E, AUX RS485, slave 247, behind a Modbus TCP gateway). Other
families are recognised by `identify()` but not read.

## Known blocker

fw Master 2.23 / Manager 1.95 drops the RTU slave-address byte; tmodbus raises
`HeaderMismatchError`. Fix belongs in tmodbus (opt-in tolerant parsing), see the
integration repo's `docs/tmodbus-missing-unit-id.md`.
