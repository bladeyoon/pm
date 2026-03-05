## Scripts Overview

This folder contains start/stop scripts for local Docker workflows on each OS:

- macOS:
  - `scripts/start-mac.sh`
  - `scripts/stop-mac.sh`
- Linux:
  - `scripts/start-linux.sh`
  - `scripts/stop-linux.sh`
- Windows:
  - `scripts/start-windows.bat`
  - `scripts/stop-windows.bat`

All scripts run from the repository root and use `docker compose` to manage the app container.