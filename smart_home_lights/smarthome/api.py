"""Optional REST service exposing light control over HTTP.

This is a thin layer over :class:`~smarthome.client.LightController` so you can
drive your lights from webhooks, phone shortcuts, or other machines on your
network. It requires the ``api`` extra::

    pip install -e ".[api]"
    uvicorn smarthome.api:app --host 0.0.0.0 --port 8099

Then, for example::

    curl -X POST localhost:8099/lights/kitchen/on -d '{"brightness_pct": 40}' \
         -H 'Content-Type: application/json'

Security note: this service has no auth of its own — it trusts anyone who can
reach the port. Keep it on your LAN, or put it behind a reverse proxy /
firewall. It holds your Home Assistant token, so do not expose it to the
public internet.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - only hit without the extra
    raise ImportError(
        "The REST API needs the 'api' extra. Install with: pip install -e \".[api]\""
    ) from exc

from .client import HomeAssistantError, LightController, NoMatchingLightsError

_controller: LightController | None = None


@asynccontextmanager
async def lifespan(app: "FastAPI"):
    global _controller
    _controller = LightController()
    try:
        yield
    finally:
        _controller.close()
        _controller = None


app = FastAPI(title="Smart Home Lights", version="0.1.0", lifespan=lifespan)


def ctrl() -> LightController:
    if _controller is None:  # pragma: no cover - defensive
        raise HTTPException(status_code=503, detail="Controller not ready")
    return _controller


class OnRequest(BaseModel):
    brightness_pct: int | None = Field(default=None, ge=0, le=100)
    rgb: tuple[int, int, int] | None = None
    color_temp_kelvin: int | None = Field(default=None, ge=1000, le=6500)
    transition: float | None = Field(default=None, ge=0)


class TransitionRequest(BaseModel):
    transition: float | None = Field(default=None, ge=0)


def _resolve(target: str) -> list[str]:
    try:
        return ctrl().resolve(target)
    except NoMatchingLightsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _light_dict(entity_id: str) -> dict[str, Any]:
    light = ctrl().get_light(entity_id)
    return {
        "entity_id": light.entity_id,
        "name": light.name,
        "state": light.state,
        "brightness_pct": light.brightness_pct,
        "rgb": light.rgb,
        "color_temp_kelvin": light.color_temp_kelvin,
    }


@app.get("/health")
def health() -> dict[str, str]:
    try:
        return {"status": "ok", "home_assistant": ctrl().ping()}
    except HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/lights")
def list_lights() -> list[dict[str, Any]]:
    try:
        return [
            {
                "entity_id": light.entity_id,
                "name": light.name,
                "state": light.state,
                "brightness_pct": light.brightness_pct,
            }
            for light in ctrl().list_lights()
        ]
    except HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/lights/{target}")
def get_lights(target: str) -> list[dict[str, Any]]:
    return [_light_dict(eid) for eid in _resolve(target)]


@app.post("/lights/{target}/on")
def turn_on(target: str, body: OnRequest | None = None) -> dict[str, Any]:
    body = body or OnRequest()
    entity_ids = _resolve(target)
    ctrl().turn_on(
        entity_ids,
        brightness_pct=body.brightness_pct,
        rgb=body.rgb,
        color_temp_kelvin=body.color_temp_kelvin,
        transition=body.transition,
    )
    return {"action": "on", "entity_ids": entity_ids}


@app.post("/lights/{target}/off")
def turn_off(target: str, body: TransitionRequest | None = None) -> dict[str, Any]:
    body = body or TransitionRequest()
    entity_ids = _resolve(target)
    ctrl().turn_off(entity_ids, transition=body.transition)
    return {"action": "off", "entity_ids": entity_ids}


@app.post("/lights/{target}/toggle")
def toggle(target: str, body: TransitionRequest | None = None) -> dict[str, Any]:
    body = body or TransitionRequest()
    entity_ids = _resolve(target)
    ctrl().toggle(entity_ids, transition=body.transition)
    return {"action": "toggle", "entity_ids": entity_ids}
