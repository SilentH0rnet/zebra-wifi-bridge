# zebra-wifi-bridge

Add WiFi printing to a USB Zebra label printer using a Raspberry Pi Zero 2 W, Flask and ZPL.

This project turns any USB-only Zebra label printer into a network-accessible
print server. A lightweight Flask API runs on a Raspberry Pi, accepts ZPL
print jobs over HTTP, and writes them directly to the printer's USB device.

## Features

- `POST /print` — send raw ZPL code, printed as-is
- `POST /print/label` — simple JSON template (text + optional barcode)
- `GET /status` — check whether the printer is connected
- API key authentication
- systemd service for autostart on boot, with automatic restart on failure

## Requirements

- Raspberry Pi (tested on a Pi Zero 2 W) with WiFi and Raspberry Pi OS
- A Zebra label printer connected via USB (tested on a Zebra ZD220t)
- Python 3 and pip

## Installation

```bash
git clone https://github.com/<your-username>/zebra-wifi-bridge.git
cd zebra-wifi-bridge

pip3 install -r requirements.txt --break-system-packages
```

Check that the printer is recognized as a USB printer device:

```bash
ls -l /dev/usb/lp0
```

Make sure your user can write to it (the device usually belongs to the `lp`
group):

```bash
sudo usermod -aG lp $USER
```

Group changes only take effect for new login sessions / newly started
services, so log out and back in (or reboot) before testing.

## Running manually

```bash
python3 app.py
```

The API listens on `0.0.0.0:8080` by default.

## Configuration

The app is configured entirely through environment variables:

| Variable             | Default          | Description                          |
|----------------------|------------------|---------------------------------------|
| `ZPL_API_KEY`         | `changeme`       | API key required in the `X-API-Key` header |
| `ZPL_PRINTER_DEVICE`  | `/dev/usb/lp0`   | Path to the printer's USB device      |
| `ZPL_HOST`            | `0.0.0.0`        | Host/interface to bind to             |
| `ZPL_PORT`            | `8080`           | Port to listen on                     |

**Change `ZPL_API_KEY` before exposing this on your network.**

## Running as a systemd service (autostart)

```bash
sudo cp zebra-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable zebra-api.service
sudo systemctl start zebra-api.service
```

Edit `zebra-api.service` first if your username or project path differs from
`pi` / `/home/pi/zebra-wifi-bridge`.

Check status and logs:

```bash
sudo systemctl status zebra-api.service
journalctl -u zebra-api.service -f
```

## Usage examples

Check printer status:

```bash
curl http://<pi-ip>:8080/status
```

Print raw ZPL:

```bash
curl -X POST http://<pi-ip>:8080/print \
     -H "X-API-Key: changeme" \
     -H "Content-Type: text/plain" \
     --data-binary "^XA^FO50,50^A0N,50,50^FDHello World^FS^XZ"
```

Print a simple label from a JSON template:

```bash
curl -X POST http://<pi-ip>:8080/print/label \
     -H "X-API-Key: changeme" \
     -H "Content-Type: application/json" \
     -d '{"text": "Test Label", "barcode": "123456789", "x": 50, "y": 50}'
```

## Makefile shortcuts

```bash
make help              # list all available commands
make install            # install Python dependencies
make service-install    # install the systemd unit
make service-enable     # enable autostart
make service-start      # start the service
make logs               # follow service logs
make status             # query printer status
make print-test          # print a test label
```

Override defaults as needed, e.g.:

```bash
make print-test PI_HOST=192.168.1.50 API_KEY=mysecretkey
```

## Troubleshooting

- **`Permission denied` writing to the printer device** — your user isn't in
  the `lp` group, or the service hasn't picked up the new group membership
  yet. Run `sudo usermod -aG lp <user>` and restart the service (or reboot).
- **`Changing to the requested working directory failed`** — the path in
  `zebra-api.service` (`WorkingDirectory` / `ExecStart`) doesn't match where
  the project actually lives. Update both to the correct path.
- **`connected: false` from `/status`** — the printer isn't detected as a USB
  device. Check the cable, make sure the printer is powered on, and run
  `dmesg | tail -20` after plugging it in.

## License

MIT
