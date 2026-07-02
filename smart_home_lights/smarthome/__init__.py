"""smarthome — control Matter/HomeKit lights through Home Assistant.

Public surface:

    from smarthome import LightController
    with LightController() as lights:
        lights.turn_on(lights.resolve("kitchen"), brightness_pct=40)
"""

from __future__ import annotations

from .client import (
    HomeAssistantError,
    LightController,
    NoMatchingLightsError,
)
from .config import ConfigError, Settings, load_settings
from .models import Light

__all__ = [
    "LightController",
    "HomeAssistantError",
    "NoMatchingLightsError",
    "Light",
    "Settings",
    "load_settings",
    "ConfigError",
]

__version__ = "0.1.0"
