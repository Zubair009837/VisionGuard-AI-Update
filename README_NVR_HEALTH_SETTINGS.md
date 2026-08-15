# VisionGuard AI - NVR Health + Settings Update

This update is applied to the current VisionGuard AI codebase.

## Added
- Live CPU telemetry for NVR-1 through NVR-9 using Hikvision `/ISAPI/System/status`.
- Live memory, temperature, uptime and connectivity telemetry where the NVR exposes those fields.
- Automatic health polling every 5 seconds.
- Automatic alerts for NVR offline, high CPU, high memory, high temperature, high storage usage and unhealthy HDD status.
- Recovery alerts when an issue clears.
- Dashboard live NVR health grid and live alert feed.
- `/alerts` API and enhanced Alerts page with severity.
- NVR Settings page with NVR selector (all 9 NVRs), Device Info, Network, Date & Time, Capabilities and an Advanced ISAPI XML editor.
- Settings are sent only to the selected NVR.
- Reboot control for the selected NVR with confirmation.
- Destructive factory-reset/firmware/configuration-data endpoints are blocked from the web settings editor.

## Live behavior
- Health/CPU polling: 5 seconds.
- Storage remains on its existing live storage monitor/refresh behavior.
- Alerts are persisted in `backend/app/alert_history.json`.

## Run
Install frontend dependencies from `frontend/package-lock.json` and start the backend/frontend as in the existing project.
