"""Field types for the FoxESS encodings the generic helpers do not cover."""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from typing import Any, Literal

from modbus_connection.model import RegisterField

__all__ = ["FirmwareVersion", "ModelStringField", "VersionField"]


@total_ordering
@dataclass(frozen=True)
class FirmwareVersion:
    """A firmware version as the inverter reports it, e.g. ``1.95``."""

    major: int
    minor: int

    def __str__(self) -> str:
        """The version as FoxESS shows it, e.g. ``1.95``."""
        return f"{self.major}.{self.minor:02d}"

    def __lt__(self, other: object) -> bool:
        """Whether this version is older than ``other``."""
        if not isinstance(other, FirmwareVersion):
            return NotImplemented
        return (self.major, self.minor) < (other.major, other.minor)


class VersionField(RegisterField[FirmwareVersion]):
    """One register holding a firmware version.

    FoxESS encodes the master and slave versions in decimal (``223`` is 2.23)
    and the manager version in hex (``0x195`` is 1.95).
    """

    def __init__(self, address: int, *, encoding: Literal["decimal", "hex"]) -> None:
        super().__init__(address)
        self.encoding = encoding

    def decode(
        self, words: list[int], scale_exponent: int | None = None
    ) -> FirmwareVersion:
        """Decode the version register."""
        word = words[0]
        if self.encoding == "hex":
            # 0x195 -> 1.95: each byte is read as the digits it shows. A byte
            # with a hex letter in it has no such reading; keep its value.
            major, minor = f"{word >> 8:x}", f"{word & 0xFF:x}"
            return FirmwareVersion(
                int(major) if major.isdecimal() else word >> 8,
                int(minor) if minor.isdecimal() else word & 0xFF,
            )
        return FirmwareVersion(word // 100, word % 100)


class ModelStringField(RegisterField[str]):
    """The model name at holding 30000 onwards.

    Most models put one ASCII character in the low byte of each register. Some
    (H1 G2, H3 Pro) pack two characters per register, high byte first. The
    string ends at the first non-printable character. The H3 pads it with
    leading spaces.
    """

    def __init__(self, address: int, *, count: int) -> None:
        super().__init__(address, count=count)

    def decode(self, words: list[int], scale_exponent: int | None = None) -> str:
        """Decode the model name."""
        chars: list[int] = []
        if words and words[0] & 0xFF00:
            for word in words:
                chars.extend(((word >> 8) & 0xFF, word & 0xFF))
        else:
            chars = list(words)
        text = ""
        for char in chars:
            if not 0x20 <= char < 0x7F:
                break
            text += chr(char)
        return text.strip()

    def encode(self, value: Any, scale_exponent: int | None = None) -> list[int]:
        """Refuse: the model name is read-only."""
        raise NotImplementedError("the model name is read-only")
