"""A small, focused client for controlling lights via the Home Assistant API.

Home Assistant exposes a REST API documented at
https://developers.home-assistant.io/docs/api/rest/. This client wraps just
the pieces needed to discover and control ``light.*`` entities, using a
long-lived access token for authentication.

The client is synchronous (built on ``httpx.Client``) which keeps the CLI
simple; the same instance is reused by the optional REST service.
"""

from __future__ import annotations

from typing import Any, Iterable

import httpx

from .config import Settings, load_settings
from .models import Light


class HomeAssistantError(RuntimeError):
    """Raised when Home Assistant returns an error or is unreachable."""


class NoMatchingLightsError(HomeAssistantError):
    """Raised when a target string matches no known light entities."""


def _pct_to_brightness(pct: int) -> int:
    """Convert a 0-100 percentage to HA's 0-255 brightness scale."""
    pct = max(0, min(100, pct))
    return round(pct / 100 * 255)


class LightController:
    """Discover and control Home Assistant light entities."""

    def __init__(self, settings: Settings | None = None, *, client: httpx.Client | None = None):
        self.settings = settings or load_settings()
        self._client = client or httpx.Client(
            base_url=self.settings.api_url,
            headers={
                "Authorization": f"Bearer {self.settings.token}",
                "Content-Type": "application/json",
            },
            verify=self.settings.verify_ssl,
            timeout=self.settings.timeout,
        )
        self._owns_client = client is None

    # -- lifecycle -------------------------------------------------------
    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "LightController":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- low level -------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise HomeAssistantError(
                f"Could not reach Home Assistant at {self.settings.base_url}: {exc}"
            ) from exc
        if response.status_code == 401:
            raise HomeAssistantError(
                "Home Assistant rejected the token (401). Check HASS_TOKEN is a "
                "valid long-lived access token."
            )
        if response.status_code >= 400:
            raise HomeAssistantError(
                f"Home Assistant returned {response.status_code} for {method} {path}: "
                f"{response.text}"
            )
        if response.content:
            return response.json()
        return None

    # -- discovery -------------------------------------------------------
    def ping(self) -> str:
        """Verify connectivity and auth. Returns HA's greeting message."""
        payload = self._request("GET", "/")
        if isinstance(payload, dict) and "message" in payload:
            return payload["message"]
        return "OK"

    def list_lights(self) -> list[Light]:
        """Return every ``light.*`` entity, sorted by friendly name."""
        states = self._request("GET", "/states") or []
        lights = [
            Light.from_state(s)
            for s in states
            if isinstance(s, dict) and str(s.get("entity_id", "")).startswith("light.")
        ]
        return sorted(lights, key=lambda light: light.name.lower())

    def get_light(self, entity_id: str) -> Light:
        payload = self._request("GET", f"/states/{entity_id}")
        return Light.from_state(payload)

    def resolve(self, target: str) -> list[str]:
        """Resolve a target string to one or more light entity_ids.

        Matching is intentionally forgiving so natural targets work:

        * exact ``entity_id`` (``light.kitchen``) -> that entity
        * ``all`` -> every light
        * otherwise, case-insensitive substring match against both the
          ``entity_id`` and the friendly name (so ``kitchen`` matches
          ``light.kitchen_ceiling`` and a light named "Kitchen Lamp").
        """
        target = target.strip()
        if not target:
            raise NoMatchingLightsError("Empty target.")

        lights = self.list_lights()

        if target.lower() == "all":
            if not lights:
                raise NoMatchingLightsError("No light entities found in Home Assistant.")
            return [light.entity_id for light in lights]

        # Exact entity_id wins outright.
        for light in lights:
            if light.entity_id == target:
                return [light.entity_id]

        needle = target.lower()
        matches = [
            light.entity_id
            for light in lights
            if needle in light.entity_id.lower() or needle in light.name.lower()
        ]
        if not matches:
            raise NoMatchingLightsError(
                f"No lights matched {target!r}. Run `smarthome list` to see available lights."
            )
        return matches

    # -- control ---------------------------------------------------------
    def _call_service(self, service: str, entity_ids: Iterable[str], **data: Any) -> None:
        entity_ids = list(entity_ids)
        payload: dict[str, Any] = {"entity_id": entity_ids}
        payload.update({k: v for k, v in data.items() if v is not None})
        self._request("POST", f"/services/light/{service}", json=payload)

    def turn_on(
        self,
        entity_ids: Iterable[str],
        *,
        brightness_pct: int | None = None,
        rgb: tuple[int, int, int] | None = None,
        color_temp_kelvin: int | None = None,
        transition: float | None = None,
    ) -> None:
        data: dict[str, Any] = {"transition": transition}
        if brightness_pct is not None:
            data["brightness"] = _pct_to_brightness(brightness_pct)
        if rgb is not None:
            data["rgb_color"] = list(rgb)
        if color_temp_kelvin is not None:
            data["color_temp_kelvin"] = color_temp_kelvin
        self._call_service("turn_on", entity_ids, **data)

    def turn_off(self, entity_ids: Iterable[str], *, transition: float | None = None) -> None:
        self._call_service("turn_off", entity_ids, transition=transition)

    def toggle(self, entity_ids: Iterable[str], *, transition: float | None = None) -> None:
        self._call_service("toggle", entity_ids, transition=transition)

    def set_brightness(self, entity_ids: Iterable[str], pct: int, *, transition: float | None = None) -> None:
        """Set brightness. ``pct == 0`` turns the light off."""
        if pct <= 0:
            self.turn_off(entity_ids, transition=transition)
        else:
            self.turn_on(entity_ids, brightness_pct=pct, transition=transition)
