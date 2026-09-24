"""Which inverter a model name describes."""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["InverterModel", "identify"]


@dataclass(frozen=True)
class InverterModel:
    """A recognised inverter model."""

    name: str
    """The model name as the inverter reports it, e.g. ``H3-10.0-E``."""
    family: str
    """The register map it speaks, e.g. ``H3``."""
    rated_power: float
    """Rated output in kW."""


# Ordered most specific first: H3-Smart and H3 Pro share the H3- prefix but
# speak other maps, and must not fall through to the plain H3.
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^H3-(\d+(?:\.\d+)?)-(?:Smart|M)\b"), "H3_SMART"),
    (re.compile(r"^H3-PRO-(\d+(?:\.\d+)?)"), "H3_PRO"),
    (re.compile(r"^H3-(\d+(?:\.\d+)?)"), "H3"),
)


def identify(model: str) -> InverterModel | None:
    """The model a model name describes; ``None`` if it is not recognised."""
    for pattern, family in _PATTERNS:
        if match := pattern.match(model):
            return InverterModel(model, family, float(match[1]))
    return None
