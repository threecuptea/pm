# Scripts AGENTS

## Purpose

The `scripts/` folder contains cross-platform scripts to start and stop the local Dockerized app.

## Current scripts

- macOS start: `scripts/start-mac.sh`
- macOS stop: `scripts/stop-mac.sh`
- Linux start: `scripts/start-linux.sh`
- Linux stop: `scripts/stop-linux.sh`
- Windows start: `scripts/start-windows.ps1`
- Windows stop: `scripts/stop-windows.ps1`

## Behavior

- Start scripts run `docker compose up --build -d` from repository root.
- Stop scripts run `docker compose down` from repository root.

## Notes

- Scripts are intentionally minimal for MVP simplicity.
- Use these scripts for manual smoke checks during development.