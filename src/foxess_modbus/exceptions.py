"""Errors this library raises on top of modbus-connection's."""

from __future__ import annotations

__all__ = ["FoxEssError", "UnsupportedModelError"]


class FoxEssError(Exception):
    """Base for errors about the inverter rather than the Modbus link."""


class UnsupportedModelError(FoxEssError):
    """The inverter answered, but its model is not one this library reads."""

    def __init__(self, model: str) -> None:
        super().__init__(f"unsupported FoxESS model {model!r}")
        self.model = model
