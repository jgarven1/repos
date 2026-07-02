"""Command-line interface for controlling Home Assistant lights.

Examples
--------
    smarthome ping                          # check the connection
    smarthome list                          # show all lights and their state
    smarthome on kitchen                    # turn on everything matching "kitchen"
    smarthome on "living room" -b 40 -t 2   # 40% brightness, 2s fade
    smarthome on desk --color 255,120,0     # warm orange
    smarthome on desk --kelvin 2700         # warm white
    smarthome off all                       # everything off
    smarthome dim bedroom 25                # set bedroom lights to 25%
    smarthome toggle office
    smarthome status kitchen
"""

from __future__ import annotations

import sys

import click

from .client import HomeAssistantError, LightController, NoMatchingLightsError
from .config import ConfigError


def _parse_rgb(ctx: click.Context, param: click.Parameter, value: str | None) -> tuple[int, int, int] | None:
    if value is None:
        return None
    parts = value.split(",")
    if len(parts) != 3:
        raise click.BadParameter("expected R,G,B (e.g. 255,120,0)")
    try:
        rgb = tuple(int(p) for p in parts)
    except ValueError:
        raise click.BadParameter("RGB components must be integers 0-255")
    if any(c < 0 or c > 255 for c in rgb):
        raise click.BadParameter("RGB components must be between 0 and 255")
    return rgb  # type: ignore[return-value]


def _controller() -> LightController:
    try:
        return LightController()
    except ConfigError as exc:
        raise click.ClickException(str(exc))


def _apply(action, target: str, *args, **kwargs) -> list[str]:
    """Resolve ``target`` and run ``action`` against the matched entities."""
    with _controller() as ctrl:
        entity_ids = ctrl.resolve(target)
        action(ctrl, entity_ids, *args, **kwargs)
        return entity_ids


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="smarthome-lights", prog_name="smarthome")
def main() -> None:
    """Control your Matter/HomeKit lights through Home Assistant."""


@main.command()
def ping() -> None:
    """Check connectivity and authentication."""
    with _controller() as ctrl:
        click.echo(f"Connected: {ctrl.ping()}")


@main.command(name="list")
def list_lights() -> None:
    """List all light entities and their current state."""
    with _controller() as ctrl:
        lights = ctrl.list_lights()
    if not lights:
        click.echo("No light entities found. Have you added your lights to Home Assistant yet?")
        return
    for light in lights:
        marker = "*" if light.is_on else " "
        click.echo(f" {marker} {light.describe()}")


@main.command()
@click.argument("target")
@click.option("-b", "--brightness", type=click.IntRange(0, 100), help="Brightness 0-100%.")
@click.option("--color", "rgb", callback=_parse_rgb, help="RGB color, e.g. 255,120,0.")
@click.option("--kelvin", type=click.IntRange(1000, 6500), help="Color temperature in Kelvin.")
@click.option("-t", "--transition", type=float, help="Fade time in seconds.")
def on(target: str, brightness: int | None, rgb, kelvin: int | None, transition: float | None) -> None:
    """Turn TARGET on (optionally set brightness/color)."""
    entity_ids = _apply(
        lambda ctrl, ids: ctrl.turn_on(
            ids,
            brightness_pct=brightness,
            rgb=rgb,
            color_temp_kelvin=kelvin,
            transition=transition,
        ),
        target,
    )
    click.echo(f"Turned on {len(entity_ids)} light(s): {', '.join(entity_ids)}")


@main.command()
@click.argument("target")
@click.option("-t", "--transition", type=float, help="Fade time in seconds.")
def off(target: str, transition: float | None) -> None:
    """Turn TARGET off."""
    entity_ids = _apply(lambda ctrl, ids: ctrl.turn_off(ids, transition=transition), target)
    click.echo(f"Turned off {len(entity_ids)} light(s): {', '.join(entity_ids)}")


@main.command()
@click.argument("target")
@click.option("-t", "--transition", type=float, help="Fade time in seconds.")
def toggle(target: str, transition: float | None) -> None:
    """Toggle TARGET."""
    entity_ids = _apply(lambda ctrl, ids: ctrl.toggle(ids, transition=transition), target)
    click.echo(f"Toggled {len(entity_ids)} light(s): {', '.join(entity_ids)}")


@main.command()
@click.argument("target")
@click.argument("percent", type=click.IntRange(0, 100))
@click.option("-t", "--transition", type=float, help="Fade time in seconds.")
def dim(target: str, percent: int, transition: float | None) -> None:
    """Set TARGET to PERCENT brightness (0 turns it off)."""
    entity_ids = _apply(lambda ctrl, ids: ctrl.set_brightness(ids, percent, transition=transition), target)
    click.echo(f"Set {len(entity_ids)} light(s) to {percent}%: {', '.join(entity_ids)}")


@main.command()
@click.argument("target")
def status(target: str) -> None:
    """Show the current state of lights matching TARGET."""
    with _controller() as ctrl:
        entity_ids = ctrl.resolve(target)
        for entity_id in entity_ids:
            click.echo(ctrl.get_light(entity_id).describe())


def run() -> None:
    """Entry point that turns library errors into clean CLI messages."""
    try:
        main()
    except (HomeAssistantError, NoMatchingLightsError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
