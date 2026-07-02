import httpx
import pytest
from click.testing import CliRunner

from smarthome.cli import main
from smarthome.client import LightController

from .conftest import STATES


@pytest.fixture
def cli_env(monkeypatch, respx_mock):
    """Point the CLI at the mocked HA and stub out states + service calls."""
    monkeypatch.setenv("HASS_URL", "http://ha.test:8123")
    monkeypatch.setenv("HASS_TOKEN", "test-token")
    respx_mock.get("http://ha.test:8123/api/states").mock(
        return_value=httpx.Response(200, json=STATES)
    )
    respx_mock.get("http://ha.test:8123/api/").mock(
        return_value=httpx.Response(200, json={"message": "API running."})
    )
    for service in ("turn_on", "turn_off", "toggle"):
        respx_mock.post(f"http://ha.test:8123/api/services/light/{service}").mock(
            return_value=httpx.Response(200, json=[])
        )
    return CliRunner()


def test_list(cli_env):
    result = cli_env.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "Kitchen Ceiling" in result.output
    assert "switch.fan" not in result.output


def test_ping(cli_env):
    result = cli_env.invoke(main, ["ping"])
    assert result.exit_code == 0
    assert "API running." in result.output


def test_on_by_name(cli_env):
    result = cli_env.invoke(main, ["on", "kitchen", "-b", "40"])
    assert result.exit_code == 0
    assert "light.kitchen_ceiling" in result.output


def test_off_all(cli_env):
    result = cli_env.invoke(main, ["off", "all"])
    assert result.exit_code == 0
    assert "3 light(s)" in result.output


def test_no_match_exits_nonzero(cli_env):
    result = cli_env.invoke(main, ["on", "garage"])
    assert result.exit_code != 0


def test_bad_rgb_rejected(cli_env):
    result = cli_env.invoke(main, ["on", "kitchen", "--color", "300,0,0"])
    assert result.exit_code != 0
    assert "between 0 and 255" in result.output


def test_missing_config_is_clean_error(monkeypatch):
    monkeypatch.delenv("HASS_URL", raising=False)
    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HOMEASSISTANT_URL", raising=False)
    monkeypatch.delenv("HASS_TOKEN", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    monkeypatch.delenv("HOMEASSISTANT_TOKEN", raising=False)
    result = CliRunner().invoke(main, ["list"])
    assert result.exit_code != 0
    assert "No Home Assistant URL" in result.output
