"""The FoxESS-specific field codecs and model recognition."""

from __future__ import annotations

import pytest

from foxess_modbus import FirmwareVersion, identify
from foxess_modbus.fields import ModelStringField, VersionField
from foxess_modbus.h3 import active_faults


@pytest.mark.parametrize(
    ("word", "encoding", "expected"),
    [
        (223, "decimal", "2.23"),
        (103, "decimal", "1.03"),
        (0x195, "hex", "1.95"),
        (0x180, "hex", "1.80"),
        (0x1A2, "hex", "1.162"),  # no decimal reading: the byte value
    ],
)
def test_version_field(word: int, encoding: str, expected: str) -> None:
    field = VersionField(0, encoding=encoding)  # type: ignore[arg-type]
    assert str(field.decode([word])) == expected


def test_versions_order() -> None:
    assert FirmwareVersion(1, 92) < FirmwareVersion(1, 93) <= FirmwareVersion(1, 95)
    assert FirmwareVersion(2, 0) > FirmwareVersion(1, 99)


def test_model_one_char_per_register() -> None:
    field = ModelStringField(0, count=15)
    words = [ord(c) for c in "   H3-10.0-E"] + [0, 0, 0]
    assert field.decode(words) == "H3-10.0-E"


def test_model_two_chars_per_register() -> None:
    field = ModelStringField(0, count=4)
    words = [(ord("H") << 8) | ord("1"), (ord("-") << 8) | ord("5"), 0x2000, 0]
    assert field.decode(words) == "H1-5"


@pytest.mark.parametrize(
    ("model", "family", "power"),
    [
        ("H3-10.0-E", "H3", 10.0),
        ("H3-5.0-E", "H3", 5.0),
        ("H3-12.0-Smart", "H3_SMART", 12.0),
        ("H3-10.0-M", "H3_SMART", 10.0),
        ("H3-PRO-15.0", "H3_PRO", 15.0),
    ],
)
def test_identify(model: str, family: str, power: float) -> None:
    found = identify(model)
    assert found is not None
    assert (found.family, found.rated_power) == (family, power)


def test_identify_unknown() -> None:
    assert identify("H1-5.0-E") is None
    assert identify("") is None


def test_active_faults() -> None:
    assert active_faults([0, 0, 0, 0, 0, 0, 0]) == []
    assert active_faults([0x0003, 0, 0, 0, 0, 0x0001, 0]) == [
        "Grid Lost Fault",
        "Grid Voltage Fault",
        "BMS External Fault",
    ]
    assert active_faults([0x0080, 0, 0, 0, 0x8000, 0, 0]) == [
        "Unknown fault 1.7",
        "Unknown fault 5.15",
    ]
