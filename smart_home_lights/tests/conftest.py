import httpx
import pytest

from smarthome.client import LightController
from smarthome.config import Settings

STATES = [
    {
        "entity_id": "light.kitchen_ceiling",
        "state": "on",
        "attributes": {"friendly_name": "Kitchen Ceiling", "brightness": 128},
    },
    {
        "entity_id": "light.living_room_lamp",
        "state": "off",
        "attributes": {"friendly_name": "Living Room Lamp"},
    },
    {
        "entity_id": "light.bedroom",
        "state": "on",
        "attributes": {
            "friendly_name": "Bedroom",
            "brightness": 255,
            "rgb_color": [255, 100, 0],
        },
    },
    # A non-light entity that must be filtered out.
    {"entity_id": "switch.fan", "state": "on", "attributes": {"friendly_name": "Fan"}},
]


@pytest.fixture
def settings() -> Settings:
    return Settings(base_url="http://ha.test:8123", token="test-token")


@pytest.fixture
def controller(settings, respx_mock):
    """A LightController wired to a mocked httpx transport."""
    respx_mock.get("http://ha.test:8123/api/states").mock(
        return_value=httpx.Response(200, json=STATES)
    )
    respx_mock.get("http://ha.test:8123/api/").mock(
        return_value=httpx.Response(200, json={"message": "API running."})
    )
    ctrl = LightController(settings=settings)
    yield ctrl
    ctrl.close()
