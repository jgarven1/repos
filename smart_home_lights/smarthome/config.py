"""Configuration loading for the Home Assistant light controller.

Settings are read from environment variables, with support for a local
``.env`` file (via python-dotenv) so credentials never live in the code or
in shell history. See ``.env.example`` for the full list.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv is optional at import time; nice-to-have, not required.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv simply not installed
    pass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Resolved connection settings for a Home Assistant instance."""

    base_url: str
    token: str
    verify_ssl: bool = True
    timeout: float = 10.0

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api"


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return None


def load_settings() -> Settings:
    """Build :class:`Settings` from the environment.

    Recognised variables (aliases accepted so this plays nicely with common
    Home Assistant tooling):

    * ``HASS_URL`` / ``HA_URL`` / ``HOMEASSISTANT_URL`` – e.g.
      ``http://homeassistant.local:8123``
    * ``HASS_TOKEN`` / ``HA_TOKEN`` – a long-lived access token
    * ``HASS_VERIFY_SSL`` – ``false`` to skip TLS verification (self-signed)
    * ``HASS_TIMEOUT`` – request timeout in seconds (default ``10``)
    """

    base_url = _first_env("HASS_URL", "HA_URL", "HOMEASSISTANT_URL")
    token = _first_env("HASS_TOKEN", "HA_TOKEN", "HOMEASSISTANT_TOKEN")

    if not base_url:
        raise ConfigError(
            "No Home Assistant URL configured. Set HASS_URL (e.g. "
            "http://homeassistant.local:8123) in your environment or .env file."
        )
    if not token:
        raise ConfigError(
            "No Home Assistant token configured. Create a long-lived access "
            "token in HA (Profile -> Security -> Long-lived access tokens) and "
            "set HASS_TOKEN in your environment or .env file."
        )

    base_url = base_url.rstrip("/")

    verify_raw = _first_env("HASS_VERIFY_SSL")
    verify_ssl = True
    if verify_raw is not None:
        verify_ssl = verify_raw.lower() not in {"0", "false", "no", "off"}

    timeout_raw = _first_env("HASS_TIMEOUT")
    timeout = 10.0
    if timeout_raw:
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise ConfigError(f"HASS_TIMEOUT must be a number, got {timeout_raw!r}") from exc

    return Settings(base_url=base_url, token=token, verify_ssl=verify_ssl, timeout=timeout)
