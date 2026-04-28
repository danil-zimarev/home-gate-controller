Pico W Hardware
==============

**Control your Raspberry Pi Pico W GPIO pins from a web browser.**

This project runs a small web server directly on the Pico W. Once you connect it to your Wi-Fi, you can open a browser on any device in the same network and
turn pins on or off without writing any code.

---

## How It Works

```
┌─────────────┐        Wi-Fi         ┌───────────────────┐
│  Browser    │ ◄──────────────────► │  Raspberry Pi     │
│  (phone /   │   http://<pico-ip>/  │  Pico W           │
│   laptop)   │                      │                   │
└─────────────┘                      │  ┌─────────────┐  │
                                     │  │  GPIO pins  │  │
                                     │  │  (relays,   │  │
                                     │  │   LEDs …)   │  │
                                     │  └─────────────┘  │
                                     └───────────────────┘
```

1. The Pico W connects to your Wi-Fi using credentials from `config.json`.
2. It starts a tiny web server on port 80.
3. You open the IP address in a browser.
4. The web page lets you toggle pins and change settings - no terminla needed.

---

## Project Structure

```
pico-hardware/
├── src/
│   ├── main.py            ← entry point, runs on boot
│   ├── web_server.py      ← HTTP routes and page rendering
│   ├── config_manager.py  ← reads / writes config.json
│   ├── pin_manager.py     ← GPIO init and toggle logic
│   ├── network_manager.py ← Wi-Fi connection and fallback AP
│   ├── log_manager.py     ← logging to daily .log files
│   ├── time_zone.py       ← Tallinn local time (EET/EEST)
│   ├── config.json        ← your settings (create from example)
│   └── lib/
│       └── microdot/      ← bundled web framework
│
├── www/
│   └── index.html         ← web UI served by the Pico
│
├── config.example.json    ← template — copy and edit this
└── deploy.sh              ← helper script to upload files
```

---

## Requirements

| What     | Details                                                                                      |
|----------|----------------------------------------------------------------------------------------------|
| Hardware | Raspberry Pi **Pico W** (must be the Wi-Fi version                                           |
| Firmware | MicroPython for Pico W — download the `.uf2` from [micropython.org](https://micropython.org) |
| Tools    | Python 3 + `mpremote` `(pip3 install mpremote)`                                              |
| Optional | Thonny IDE - easier for begginers                                                            |

---

## Quick Start

### Step 1 – Flash MicroPython

1. Hold the **BOOTSEL** button on the Pico W.
2. Plug it into your computer via a USB cable. Keep holding the button.
3. A USB drive named `RPI-RP2` will appear. Release the button.
4. Copy the downloaded `micropython.uf2` file onto the `RPI-RP2` drive.
5. The Pico will reboot automatically into MicroPython.

### Step 2 – Create Your Config

```bash
cp src/config.example.json src/config.json
```

Then open `src/config.json` and fill in your details:

```json
{
  "wifi": {
    "ssid": "YourNetworkName",
    "password": "YourNetworkPassword",
    "ip": "",
    "mask": "",
    "gw": "",
    "dns": ""
  },
  "pins": {
    "LED": {"enabled": true, "is_active_low": false},
    "0": {"enabled": false, "is_active_low": false},
    "1": {"enabled": false, "is_active_low": false}
  }
}
```

> **Tip:** Leave the `ip`, `mask`, `gw`, and `dns` fields empty to use DHCP (automatic IP).
> Fill them only if you want to set a static IP address for your Pico.

### Step 3 – Upload Files to the Pico

```bash
# Install mpremote if you don't have it
pip3 install mpremote

# Copy everything from src/ to the Pico
mpremote connect usb fs cp -r src/ :/

# Reboot the Pico to run the code
mpremote connect usb reset
```

### Step 4 – Open the Web UI

Find the IP address your router gave to the Pico (check your router's device list, or set a static IP in the `config.json`). Then open a browser and go to:

```
http://<pico-ip>/
```

---

## Web UI – What you can do

```
┌─────────────────────────────────────────────┐
│  Pico Control Page                          │
│─────────────────────────────────────────────│
│  01 — Network Configuration                 │
│       SSID / Password / IP / Mask / GW / DNS│
│       [ Save Network ]                      │
│─────────────────────────────────────────────│
│  02 — Configure Pins                        │
│       ☑ GPIO 0   ☑ GPIO 1   ☐ GPIO LED  …   │
│       [ Save Pins ]                         │
│─────────────────────────────────────────────│
│  03 — Toggle Pins                           │
│       GPIO 0  [ ON  ]                       │
│       GPIO 1  [ OFF ]                       │
│─────────────────────────────────────────────│
│  [ ↓ Logs ]   [ ↺ Reboot ]                  │
└─────────────────────────────────────────────┘
```

| Section                   | What it does                                                                                   |
|---------------------------|------------------------------------------------------------------------------------------------|
| **Network Configuration** | Change Wi-Fi credentials or set a static IP. Changes are saved to `config.json` on the device. |
| **Configure Pins**        | Choose which GPIO pins are active. Inactive pins are hidden from the toggle list.              |
| **Toggle Pins**           | Click a pin row to switch it on or off instantly. The button shows the current state.          |
| **Logs**                  | Downloads all log files as a `.zip` archive.                                                   |
| **Reboot**                | Restarts the Pico remotely. The page reloads automatically after ~10 seconds.                  |

---

## API Endpoints

| Method | Path            | Description                                    |
|--------|-----------------|------------------------------------------------|
| `GET`  | `/`             | Serves the main web UI                         |
| `POST` | `/toggle/<pin>` | Toggles a pin; returns `{"state": true/false}` |
| `POST` | `/save_network` | Updates Wi-Fi settings                         |
| `POST` | `/save_pins`    | Updates which pins are enabled                 |
| `GET`  | `/logs`         | Returns log file contents as JSON              |
| `GET`  | `/reload`       | Reboots the Pico after 1 second                |

 
---

## Boot Sequence

```
Power on
   │
   ▼
init_pins()          ← set up GPIO outputs
   │
   ▼
connect_to_wifi()    ← try to join saved network (5 retries, 2s each)
   │
   ├─ success ──► sync NTP time ──► apply static IP (if set)
   │
   └─ failure ──► start_ap()    ──► open Wi-Fi hotspot "PicoW"
                                    (connect at 192.168.4.1)
   │
   ▼
Start web server + background tasks:
   ├── keep_wifi()        checks connection every 5 min
   ├── log_network_state() writes status every hour
   └── periodic_cleanup() deletes logs older than 7 days
```

 
---

## Pin Behaviour

| Pin number  | Type         | Default state    | Notes                                                 |
|-------------|--------------|------------------|-------------------------------------------------------|
| `LED`       | Built-in LED | OFF              | Toggles on boot to confirm startup                    |
| `0` – `15`  | Active-high  | LOW (off)        | Standard digital output                               |
| `16` – `28` | Active-low   | HIGH (relay off) | Common relay modules are active-low — HIGH = safe/off |

> **Important:** Pins 16 and above are assumed to drive relays. The safe default is HIGH (relay coil not energised). Always check your wiring before enabling these pins.
> Can be configured from `config.json`
 
---

## Logs

Log files are stored on the Pico at `logs/YYYY-MM-DD.log`. Each line looks like:

```
2025-04-28 - 14:32:05 | Network status: connected, ('192.168.1.42', ...)
2025-04-28 - 14:00:00 | SYSTEM | Boot sequence finished in 3421ms
```

Logs older than 7 days are deleted automatically to save flash storage space.
 
---

## Using the Deploy Script (Optional)

The `deploy.sh` script minifies `index.html` before uploading, which saves storage on the Pico.

```bash
# Install the Python minifier
pip3 install minify-html
 
# Run the script with your serial port
chmod +x deploy.sh
./deploy.sh /dev/ttyACM0
```

 
---

## Fallback Access Point

If the Pico cannot connect to your Wi-Fi, it creates its own open hotspot:

| Setting             | Value         |
|---------------------|---------------|
| Network name (SSID) | `PicoW`       |
| Password            | none (open)   |
| Pico IP address     | `192.168.4.1` |

Connect your device to `PicoW`, then open `http://192.168.4.1/` to update the Wi-Fi settings.
 
---

## Security Notice

This project is designed for use on **small, trusted home or lab networks**. The web UI has no login or password protection. Do not connect the Pico W directly to the internet or to networks you do not control.
 
---

## Troubleshooting

| Problem | What to try |
|---------|------------|
| Can't find the Pico's IP | Check your router's connected devices list, or set a static IP in `config.json` |
| Wi-Fi keeps failing | Double-check `ssid` and `password` in `config.json`; the Pico is case-sensitive |
| Pins don't respond | Make sure the pin has `"enabled": true` in `config.json` and click **Save Pins** |
| Page won't load after reboot | Wait ~10 seconds for the Pico to reconnect to Wi-Fi |
| Relay stays on after reboot | Pins ≥ 16 default to HIGH on boot (relay off). This is intentional. |
 
---

*pico-w controller v1.0 · MicroPython · Microdot*
