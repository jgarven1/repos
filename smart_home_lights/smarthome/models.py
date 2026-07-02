"""Lightweight data models for Home Assistant light entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _pct_from_brightness(brightness: Any) -> int | None:
    """Convert HA's 0-255 brightness to a 0-100 percentage."""
    if brightness is None:
        return None
    try:
        return round(int(brightness) / 255 * 100)
    except (TypeError, ValueError):
        return None


@dataclass
class Light:
    """A single Home Assistant ``light.*`` entity.

    Built from the JSON returned by ``/api/states``. We keep the raw
    attributes around so callers can reach fields we don't model explicitly.
    """

    entity_id: str
    state: str  # "on", "off", or "unavailable"
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_state(cls, payload: dict[str, Any]) -> "Light":
        return cls(
            entity_id=payload["entity_id"],
            state=payload.get("state", "unknown"),
            attributes=payload.get("attributes", {}) or {},
        )

    @property
    def name(self) -> str:
        return self.attributes.get("friendly_name", self.entity_id)

    @property
    def is_on(self) -> bool:
        return self.state == "on"

    @property
    def is_available(self) -> bool:
        return self.state not in {"unavailable", "unknown"}

    @property
    def brightness_pct(self) -> int | None:
        return _pct_from_brightness(self.attributes.get("brightness"))

    @property
    def rgb(self) -> tuple[int, int, int] | None:
        value = self.attributes.get("rgb_color")
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return tuple(int(c) for c in value)  # type: ignore[return-value]
        return None

    @property
    def color_temp_kelvin(self) -> int | None:
        value = self.attributes.get("color_temp_kelvin")
        return int(value) if value is not None else None

    def describe(self) -> str:
        """A compact one-line summary for CLI output."""
        if not self.is_available:
            return f"{self.name} [{self.entity_id}]: unavailable"
        bits = [self.state]
        if self.is_on:
            if self.brightness_pct is not None:
                bits.append(f"{self.brightness_pct}%")
            if self.rgb is not None:
                bits.append("rgb" + str(self.rgb))
            elif self.color_temp_kelvin is not None:
                bits.append(f"{self.color_temp_kelvin}K")
        return f"{self.name} [{self.entity_id}]: {', '.join(bits)}"
