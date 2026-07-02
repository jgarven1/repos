import httpx
import pytest

from smarthome.client import (
    HomeAssistantError,
    LightController,
    NoMatchingLightsError,
    _pct_to_brightness,
)
from smarthome.config import Settings
from smarthome.models import Light


def test_pct_to_brightness_bounds():
    assert _pct_to_brightness(0) == 0
    assert _pct_to_brightness(100) == 255
    assert _pct_to_brightness(50) == 128  # 127.5 rounds to 128
    assert _pct_to_brightness(150) == 255  # clamped
    assert _pct_to_brightness(-10) == 0  # clamped


def test_light_model_from_state():
    light = Light.from_state(
        {
            "entity_id": "light.bedroom",
            "state": "on",
            "attributes": {"friendly_name": "Bedroom", "brightness": 255, "rgb_color": [255, 100, 0]},
        }
    )
    assert light.name == "Bedroom"
    assert light.is_on
    assert light.brightness_pct == 100
    assert light.rgb == (255, 100, 0)
    assert "Bedroom" in light.describe()


def test_ping(controller):
    assert controller.ping() == "API running."


def test_list_lights_filters_non_lights(controller):
    lights = controller.list_lights()
    ids = [light.entity_id for light in lights]
    assert "switch.fan" not in ids
    assert ids == ["light.bedroom", "light.kitchen_ceiling", "light.living_room_lamp"]


def test_resolve_exact_entity_id(controller):
    assert controller.resolve("light.bedroom") == ["light.bedroom"]


def test_resolve_substring_matches_name_and_id(controller):
    assert controller.resolve("kitchen") == ["light.kitchen_ceiling"]
    assert controller.resolve("living") == ["light.living_room_lamp"]


def test_resolve_all(controller):
    assert len(controller.resolve("all")) == 3


def test_resolve_no_match_raises(controller):
    with pytest.raises(NoMatchingLightsError):
        controller.resolve("garage")


def test_turn_on_sends_correct_payload(controller, respx_mock):
    route = respx_mock.post("http://ha.test:8123/api/services/light/turn_on").mock(
        return_value=httpx.Response(200, json=[])
    )
    controller.turn_on(["light.kitchen_ceiling"], brightness_pct=40, transition=2)
    assert route.called
    body = route.calls.last.request.content
    import json

    payload = json.loads(body)
    assert payload["entity_id"] == ["light.kitchen_ceiling"]
    assert payload["brightness"] == _pct_to_brightness(40)
    assert payload["transition"] == 2
    # None values must be stripped, not sent as null.
    assert "rgb_color" not in payload


def test_set_brightness_zero_turns_off(controller, respx_mock):
    off_route = respx_mock.post("http://ha.test:8123/api/services/light/turn_off").mock(
        return_value=httpx.Response(200, json=[])
    )
    controller.set_brightness(["light.bedroom"], 0)
    assert off_route.called


def test_unauthorized_raises(settings, respx_mock):
    respx_mock.get("http://ha.test:8123/api/states").mock(return_value=httpx.Response(401))
    ctrl = LightController(settings=settings)
    with pytest.raises(HomeAssistantError, match="401"):
        ctrl.list_lights()
    ctrl.close()


def test_network_error_wrapped(settings, respx_mock):
    respx_mock.get("http://ha.test:8123/api/states").mock(
        side_effect=httpx.ConnectError("boom")
    )
    ctrl = LightController(settings=settings)
    with pytest.raises(HomeAssistantError, match="Could not reach"):
        ctrl.list_lights()
    ctrl.close()
