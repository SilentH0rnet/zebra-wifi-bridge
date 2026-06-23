# Makefile für zebra-wifi-bridge
# Führt gängige Setup-, Service- und Test-Aufgaben aus.
#
# Anpassen falls nötig:
PI_USER     ?= pi
INSTALL_DIR ?= /home/$(PI_USER)/zebra-api
SERVICE     := zebra-api.service
API_KEY     ?= changeme
PI_HOST     ?= raspberrypi.local
PORT        ?= 8080

.PHONY: help install run service-install service-enable service-start \
        service-stop service-restart service-status logs status print-test clean

help: ## Zeigt diese Hilfe an
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Python-Abhängigkeiten installieren
	pip3 install -r requirements.txt --break-system-packages

run: ## API direkt im Vordergrund starten (zum Testen, ohne systemd)
	ZPL_API_KEY=$(API_KEY) python3 app.py

service-install: ## systemd-Unit installieren und Daemon neu laden
	sudo cp zebra-api.service /etc/systemd/system/
	sudo systemctl daemon-reload

service-enable: ## Autostart beim Booten aktivieren
	sudo systemctl enable $(SERVICE)

service-start: ## Service jetzt starten
	sudo systemctl start $(SERVICE)

service-stop: ## Service stoppen
	sudo systemctl stop $(SERVICE)

service-restart: ## Service neu starten (z.B. nach Code-Änderung)
	sudo systemctl restart $(SERVICE)

service-status: ## Aktuellen Service-Status anzeigen
	sudo systemctl status $(SERVICE)

logs: ## Live-Logs des Service anzeigen
	journalctl -u $(SERVICE) -f

status: ## Druckerstatus über die API abfragen
	curl -s http://$(PI_HOST):$(PORT)/status | python3 -m json.tool

print-test: ## Testlabel an den Drucker schicken
	curl -X POST http://$(PI_HOST):$(PORT)/print \
		-H "X-API-Key: $(API_KEY)" \
		-H "Content-Type: text/plain" \
		--data-binary "^XA^FO50,50^A0N,50,50^FDTest 123^FS^XZ"

clean: ## Python-Cache-Dateien entfernen
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
