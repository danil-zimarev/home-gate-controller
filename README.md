pico-hardware
==============

Small MicroPython project for controlling GPIOs on a Raspberry Pi Pico W via a minimal web UI.

Overview
--------
- This project runs on the Raspberry Pi Pico W (RP2040 + CYW43439 Wi‑Fi chip).
- It uses MicroPython and a tiny web framework (Microdot, included under `src/lib/microdot`).
- The web UI (served from `www/index.html`) allows enabling/disabling configured pins and toggling them.

Repository layout (important files)
----------------------------------
- src/main.py           -- application entrypoint (should be copied to the Pico as `main.py`)
- src/web_server.py     -- web handlers and endpoints
- src/config.json       -- default configuration (Wi‑Fi, pin definitions)
- src/pin_manager.py    -- GPIO initialization and toggle helpers
- src/lib/microdot/*    -- bundled Microdot web microframework
- www/index.html        -- frontend HTML used by the web server
- tools/deploy.sh       -- helper script (optional) to deploy files to device

Requirements
------------
- Hardware: Raspberry Pi Pico W (not the non‑W Pico)
- MicroPython firmware for the Pico W (download the UF2 from https://micropython.org)
- Host machine tools to upload files to the Pico:
  - Recommended: mpremote (part of the pyboard tools)
  - Alternative: Thonny, rshell, ampy
- Python 3 on your host to install mpremote: pip3 install mpremote

Quick start (recommended using mpremote)
---------------------------------------
1. Flash MicroPython on the Pico W
   - Put the Pico W into bootloader mode: hold BOOTSEL while plugging it into USB.
   - Copy the Pico W MicroPython UF2 file (from micropython.org) to the mounted USB drive.
   - The Pico will reboot into MicroPython.

2. Install mpremote on your host (if you don't have it):

```bash
pip3 install mpremote
```

3. Copy the project files to the Pico. From the repository root run:

```bash
# Copy all files under src/ to the device root (recursively)
mpremote connect usb fs cp -r src/ :/

# Alternatively, if `mpremote connect usb` isn't detecting your device, specify the port:
# mpremote connect /dev/tty.usbmodemXXXX fs cp -r src/ :/
```

Notes:
- The command above will copy files such that `main.py`, `web_server.py`, `config.json`, and `lib/` appear at the Pico's root.
- `main.py` is executed automatically on boot by MicroPython, so after copying you can reset the board to start the app:

```bash
mpremote connect usb reset
```

4. (Optional) Use the included deploy script
   - There's a helper script at `tools/deploy.sh`. It may wrap common copy/reset steps for your environment. You can run it from the repo root:

```bash
chmod +x tools/deploy.sh
./tools/deploy.sh <device_path>
```

Configure Wi‑Fi and pins
------------------------
- Start from the provided example `src/config.example.json`. Copy it to `src/config.json` and edit the copy with your Wi‑Fi credentials and which pins you want enabled. The application reads `src/config.json` at runtime.

```bash
# make an editable config from the example
cp src/config.example.json src/config.json
# then edit the file using your editor, e.g.:
# nano src/config.json
```

- Example `src/config.example.json` (replace the placeholders before use):

```json
{
  "wifi": {
    "ssid": "YOUR_SSID",
    "password": "YOUR_PASSWORD",
    "ip": "",
    "mask": "",
    "gw": "",
    "dns": ""
  },
  "pins": {
    "LED": {"enabled": true},
    "0": {"enabled": true},
    "1": {"enabled": true},
    "16": {"enabled": false}
  }
}
```

- Important notes:
  - Remove the placeholder values (e.g. "YOUR_SSID") and put real strings before uploading the file.
  - Pins with numeric names >= 16 are treated as active‑low relays in the code (safe default: relay off). Verify wiring before enabling them.
  - The app only shows and allows toggling for pins that exist in the `pins` object and have `enabled: true`.
  - If you want to set a static IP, fill in `ip`, `mask`, `gw`, and `dns`; otherwise leave them empty to use DHCP.

Accessing the web UI
--------------------
- The device will connect to Wi‑Fi using values in `config.json`. You can either set a static IP in the config or let DHCP assign an IP.
- Once connected, open a browser to ```http://<ip>/``` (the root endpoint serves `index.html`).
- If using in AP mode default ip is ```192.168.4.1```
- Useful endpoints:
  - GET /            -- index page
  - POST /toggle/<pin>  -- toggle a pin (used by the UI)
  - POST /save_network  -- save Wi‑Fi settings
  - POST /save_pins     -- save which pins are enabled
  - GET /logs           -- retrieve logs
  - GET /reload         -- reboot the Pico

Development tips
----------------
- Use Thonny as an easier alternative for interactive development — it can open a MicroPython REPL and upload files.
- If you change `main.py` or any module and want the changes to take effect, copy the files and reset the board (or `mpremote reset`).

Security and safety
-------------------
- Pins >=16 are treated as active‑low by default because they're commonly used to drive relays. Verify wiring before enabling pins.
- This project is intended for small, trusted networks. Do not expose the Pico's web UI to untrusted networks without adding authentication.

Further changes
---------------
- To add/remove pins, edit `src/config.json` and use the UI or re-upload the file.
- To extend functionality, `web_server.py` contains the route handlers and can be modified to add new endpoints.
