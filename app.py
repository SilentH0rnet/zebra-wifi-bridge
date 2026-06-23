#!/usr/bin/env python3
"""
Zebra ZPL Print-API für Raspberry Pi Zero 2 W
-----------------------------------------------
Macht einen USB-Zebra-Drucker (ohne WLAN) über eine kleine HTTP-API
im Netzwerk verfügbar. Roher ZPL-Code wird direkt an das USB-Device
geschrieben.

Voraussetzungen auf dem Pi:
  sudo apt update
  sudo apt install python3-pip
  pip3 install flask --break-system-packages

  # Prüfen, ob der Drucker als USB-Druckergerät erkannt wird:
  ls -l /dev/usb/lp*
  # -> sollte z.B. /dev/usb/lp0 anzeigen, sobald der Zebra per USB
  #    angeschlossen und eingeschaltet ist.

  # Rechte setzen, damit der Pi-User schreiben darf (einmalig, als root):
  sudo usermod -aG lp $USER
  # danach einmal neu einloggen / reboot

Start:
  python3 app.py
  # läuft auf 0.0.0.0:8080

Beispielaufruf von einem anderen Rechner im selben WLAN:
  curl -X POST http://<pi-ip>:8080/print \
       -H "X-API-Key: changeme" \
       -H "Content-Type: text/plain" \
       --data-binary "^XA^FO50,50^A0N,50,50^FDHallo Welt^FS^XZ"
"""

import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
PRINTER_DEVICE = os.environ.get("ZPL_PRINTER_DEVICE", "/dev/usb/lp0")
API_KEY = os.environ.get("ZPL_API_KEY", "changeme")  # unbedingt ändern!
HOST = os.environ.get("ZPL_HOST", "0.0.0.0")
PORT = int(os.environ.get("ZPL_PORT", "8080"))


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def require_api_key():
    """Gibt None zurück wenn ok, sonst ein (response, status) Tupel."""
    key = request.headers.get("X-API-Key")
    if key != API_KEY:
        return jsonify({"error": "ungültiger oder fehlender API-Key"}), 401
    return None


def send_zpl(zpl_bytes: bytes):
    """Schreibt rohe ZPL-Bytes direkt auf das USB-Druckergerät."""
    if not os.path.exists(PRINTER_DEVICE):
        raise FileNotFoundError(
            f"Druckergerät {PRINTER_DEVICE} nicht gefunden. "
            f"Ist der Zebra per USB angeschlossen und eingeschaltet?"
        )
    with open(PRINTER_DEVICE, "wb") as f:
        f.write(zpl_bytes)
        f.flush()


def build_label_zpl(text: str, barcode: str | None, x: int = 50, y: int = 50) -> str:
    """Sehr einfaches Label-Template: Text + optionaler Code128-Barcode."""
    zpl = "^XA\n"
    zpl += f"^FO{x},{y}^A0N,40,40^FD{text}^FS\n"
    if barcode:
        zpl += f"^FO{x},{y + 60}^BCN,80,Y,N,N\n^FD{barcode}^FS\n"
    zpl += "^XZ\n"
    return zpl


# ---------------------------------------------------------------------------
# Routen
# ---------------------------------------------------------------------------
@app.route("/status", methods=["GET"])
def status():
    exists = os.path.exists(PRINTER_DEVICE)
    return jsonify({
        "printer_device": PRINTER_DEVICE,
        "connected": exists,
        "timestamp": time.time(),
    }), (200 if exists else 503)


@app.route("/print", methods=["POST"])
def print_raw():
    """Nimmt rohen ZPL-Code im Request-Body entgegen (Content-Type: text/plain)."""
    auth_error = require_api_key()
    if auth_error:
        return auth_error

    zpl_data = request.get_data()
    if not zpl_data:
        return jsonify({"error": "kein ZPL-Inhalt im Body"}), 400

    try:
        send_zpl(zpl_data)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except OSError as e:
        return jsonify({"error": f"Schreibfehler auf Drucker: {e}"}), 500

    return jsonify({"status": "ok", "bytes_sent": len(zpl_data)}), 200


@app.route("/print/label", methods=["POST"])
def print_label():
    """
    Einfaches Template-basiertes Drucken.
    JSON-Body: { "text": "...", "barcode": "...", "x": 50, "y": 50 }
    """
    auth_error = require_api_key()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    if not text:
        return jsonify({"error": "Feld 'text' ist erforderlich"}), 400

    barcode = payload.get("barcode")
    x = int(payload.get("x", 50))
    y = int(payload.get("y", 50))

    zpl = build_label_zpl(text, barcode, x, y)

    try:
        send_zpl(zpl.encode("utf-8"))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except OSError as e:
        return jsonify({"error": f"Schreibfehler auf Drucker: {e}"}), 500

    return jsonify({"status": "ok", "zpl_sent": zpl}), 200


if __name__ == "__main__":
    print(f"Zebra-API läuft auf http://{HOST}:{PORT}")
    print(f"Druckergerät: {PRINTER_DEVICE}")
    app.run(host=HOST, port=PORT, debug=False)
