# Smart Home Lights

Control your **Matter** lights (the ones connected through your Apple TV 4K /
Apple Home) programmatically from Python — a reusable client, a CLI, and an
optional REST service.

Apple Home / HomeKit has no open API we can call. The trick is that **Matter
supports "multi-admin"**: a single Matter device can be paired to more than one
controller at the same time. So we add a second controller — **Home
Assistant** — alongside Apple Home. Your iPhone, Siri, and existing HomeKit
automations keep working exactly as before; we just gain a programmable way in.

```
  Matter light bulb  ──┬── Apple TV 4K (Apple Home)   ← keeps working
                       └── Home Assistant (Matter)    ← this project talks to HA
                                  ▲
                                  │ REST + long-lived token
                       ┌──────────┴───────────┐
                       │  smarthome (Python)   │  CLI · library · REST API
                       └──────────────────────┘
```

---

## 1. Prerequisites

- Your Matter lights, already working in Apple Home via the Apple TV 4K hub.
- An **always-on Mac or PC on the same local network / Wi-Fi** as the lights.
  Matter is a local-network protocol, so the machine running Home Assistant
  must be on the same LAN (and ideally have a Thread border router nearby if
  your bulbs are Thread-based — the Apple TV 4K already provides one).
- Python 3.10+.

## 2. Install Home Assistant

The simplest route on a Mac/PC is Docker:

```bash
docker run -d --name homeassistant --restart unless-stopped \
  --network host \
  -v "$PWD/ha-config:/config" \
  ghcr.io/home-assistant/home-assistant:stable
```

> `--network host` matters: Matter/Thread discovery uses mDNS and IPv6 on the
> local network, which needs host networking. On macOS, where `--network host`
> is limited, running Home Assistant OS in a small VM (or on a Raspberry Pi) is
> the more reliable option — see the HA docs for
> [installation methods](https://www.home-assistant.io/installation/).

Open `http://localhost:8123` (or `http://<machine-ip>:8123`) and complete the
onboarding wizard.

## 3. Add the Matter integration

1. In Home Assistant: **Settings → Devices & Services → Add Integration → Matter**.
2. Accept the prompt to install the **Matter Server** add-on (or run it as a
   container). This is what actually speaks Matter to your bulbs.

## 4. Share each light with Home Assistant (multi-admin)

For every light you want to control, hand Home Assistant a pairing code from
Apple Home:

1. On your iPhone, open the **Home** app → tap the accessory → gear icon →
   **Turn On Pairing Mode** (sometimes shown as "Add to other platform" /
   "Pair Accessory"). Apple displays a **numeric or QR pairing code**.
2. In Home Assistant → **Settings → Devices & Services → Matter → Add device**,
   and enter that code.

The light now appears in Home Assistant as a `light.*` entity **and** stays in
Apple Home. Repeat per light.

## 5. Create a long-lived access token

In Home Assistant, click your **profile** (bottom-left) → **Security** tab →
**Long-lived access tokens** → **Create Token**. Copy it.

---

## 6. Install & configure this project

```bash
cd smart_home_lights
python3 -m venv .venv && source .venv/bin/activate
pip install -e .            # add ".[api]" for the REST service, ".[dev]" for tests

cp .env.example .env        # then edit .env:
#   HASS_URL=http://homeassistant.local:8123
#   HASS_TOKEN=<the token you just created>
```

## 7. Use it

### CLI

```bash
smarthome ping                         # verify connection + auth
smarthome list                         # list all lights and their state

smarthome on kitchen                   # match by name/entity substring
smarthome on "living room" -b 40 -t 2  # 40% brightness, 2-second fade
smarthome on desk --color 255,120,0    # warm orange
smarthome on desk --kelvin 2700        # warm white
smarthome dim bedroom 25               # set to 25% (0 turns off)
smarthome off all                      # everything off
smarthome toggle office
smarthome status kitchen
```

Targets are forgiving: an exact `entity_id` (`light.kitchen_ceiling`), the word
`all`, or any case-insensitive substring matched against both entity ids and
friendly names (so `bedroom` hits every bedroom light at once).

### As a library

```python
from smarthome import LightController

with LightController() as lights:
    for light in lights.list_lights():
        print(light.describe())

    lights.turn_on(lights.resolve("kitchen"), brightness_pct=40, transition=2)
    lights.turn_off(lights.resolve("all"))
```

### Optional REST service

```bash
pip install -e ".[api]"
uvicorn smarthome.api:app --host 0.0.0.0 --port 8099

curl -X POST localhost:8099/lights/kitchen/on \
     -H 'Content-Type: application/json' -d '{"brightness_pct": 40}'
curl -X POST localhost:8099/lights/all/off
curl localhost:8099/lights            # list
```

> The REST service has **no auth of its own** and holds your HA token — keep it
> on your LAN, never expose it to the public internet.

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

Tests mock the Home Assistant HTTP API (via `respx`), so they need no real HA
instance.

---

## Where to go next

- **Automations**: schedule scenes (sunset dim, wake-up fade) as a small loop
  or cron job calling the library — or just build them in Home Assistant's own
  automation editor, which this setup unlocks.
- **Areas/rooms**: group lights by HA *area* for room-level targeting.
- **Auth on the REST API**: add an API key/reverse proxy if you want to reach it
  from outside the LAN.

## Troubleshooting

- **`ping` fails / connection refused** — check `HASS_URL` is reachable from
  this machine (`curl $HASS_URL`), and that you're on the same network.
- **401 Unauthorized** — the token is wrong or was revoked; create a new one.
- **A light won't pair with HA** — make sure you started pairing mode *in Apple
  Home* to get a fresh code; codes are single-use.
- **Lights missing from `list`** — confirm they show up under Settings →
  Devices & Services → Matter in Home Assistant.
