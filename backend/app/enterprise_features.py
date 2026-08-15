"""VisionGuard AI enterprise extensions.

Adds NVR user discovery, camera movement tracking, camera bulk/single
configuration helpers and persistent movement history without replacing the
existing monitoring engines.
"""
from __future__ import annotations

import json
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
from requests.auth import HTTPDigestAuth

from .config import NVRS
from .alert_manager import add_alert
from .email_service import send_camera_migration_email

BASE_DIR = Path(__file__).resolve().parent
MOVEMENT_FILE = BASE_DIR / "camera_movement_history.json"
MOVEMENT_STATE_FILE = BASE_DIR / "camera_assignment_state.json"
MOVEMENT_PENDING_FILE = BASE_DIR / "camera_assignment_pending.json"
MOVEMENT_CONFIRMATION_SECONDS = 600  # camera must remain on the new NVR for 10 minutes
LOCK = threading.RLock()


def _load_json(path: Path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:
        print(f"[ENTERPRISE] JSON read error {path.name}: {exc}")
    return default


def _save_json(path: Path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False, default=str)
    tmp.replace(path)


def _now():
    return datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")


def _nvr_request(nvr: dict, method: str, endpoint: str, body=None):
    url = f"http://{nvr['ip']}:{nvr['port']}{endpoint}"
    return requests.request(
        method,
        url,
        auth=HTTPDigestAuth(nvr["username"], nvr["password"]),
        data=body.encode("utf-8") if isinstance(body, str) else body,
        headers={"Accept": "application/xml", "Content-Type": "application/xml"},
        timeout=12,
    )


def nvr_users() -> List[dict]:
    """Discover users from every configured NVR."""
    result = []
    for nvr in NVRS:
        entry = {
            "nvr": nvr["name"],
            "nvr_id": nvr["id"],
            "ip": nvr["ip"],
            "status": "ONLINE",
            "user_count": 0,
            "users": [],
        }
        try:
            r = _nvr_request(nvr, "GET", "/ISAPI/Security/users")
            if not r.ok:
                entry["status"] = f"HTTP {r.status_code}"
                result.append(entry)
                continue
            root = ET.fromstring(r.text)
            users = []
            nodes = root.findall(".//{*}User")
            if not nodes and root.tag.endswith("User"):
                nodes = [root]
            for node in nodes:
                def txt(*names):
                    for name in names:
                        child = node.find(f"{{*}}{name}")
                        if child is not None and child.text:
                            return child.text.strip()
                    return ""
                users.append({
                    "id": txt("id"),
                    "userName": txt("userName", "username"),
                    "role": txt("userLevel", "role"),
                    "enabled": txt("enabled", "enable") or "true",
                    "ipAddress": txt("ipAddress"),
                })
            entry["users"] = users
            entry["user_count"] = len(users)
        except Exception as exc:
            entry["status"] = "ERROR"
            entry["error"] = str(exc)
        result.append(entry)
    return result


def _camera_key(camera: dict) -> str:
    # Camera name is the most useful stable identity in a multi-NVR migration
    # scenario; IP is retained as a fallback for unnamed cameras.
    name = str(camera.get("name", "")).strip().lower()
    ip = str(camera.get("ip", "")).strip()
    if name and not name.startswith("camera "):
        return f"name:{name}"
    return f"ip:{ip}" if ip else f"channel:{camera.get('id')}"


def track_camera_assignment(camera: dict):
    """Confirm an NVR/channel move only after it remains stable for 10 minutes.

    A transient discovery on another recorder is kept as a pending candidate.
    The move is written to history, surfaced in Analytics and emailed only after
    the same camera is continuously discovered under the new NVR for 600 seconds.
    If it returns to the previous NVR before confirmation, the candidate is cleared.
    """
    key = _camera_key(camera)
    now_dt = datetime.now()
    current = {
        "identity": key,
        "camera": camera.get("name", "Unknown Camera"),
        "ip": camera.get("ip", ""),
        "nvr": camera.get("nvr", "Unknown NVR"),
        "channel": camera.get("id"),
        "last_seen": _now(),
    }

    with LOCK:
        state = _load_json(MOVEMENT_STATE_FILE, {})
        pending = _load_json(MOVEMENT_PENDING_FILE, {})
        previous = state.get(key)

        # First sighting establishes the confirmed baseline.
        if not previous:
            state[key] = current
            pending.pop(key, None)
            _save_json(MOVEMENT_STATE_FILE, state)
            _save_json(MOVEMENT_PENDING_FILE, pending)
            return None

        # Same NVR means the camera is stable; cancel any transient candidate.
        if previous.get("nvr") == current["nvr"]:
            if key in pending:
                pending.pop(key, None)
                _save_json(MOVEMENT_PENDING_FILE, pending)
            state[key] = current
            _save_json(MOVEMENT_STATE_FILE, state)
            return None

        # Camera is being seen on a different NVR. Start/continue the 10-minute
        # confirmation timer. Do not update the confirmed baseline yet.
        candidate = pending.get(key)
        if not candidate or candidate.get("nvr") != current["nvr"] or candidate.get("channel") != current.get("channel"):
            pending[key] = {
                "started_at": now_dt.isoformat(),
                "candidate": current,
                "confirmation_seconds": MOVEMENT_CONFIRMATION_SECONDS,
            }
            _save_json(MOVEMENT_PENDING_FILE, pending)
            return None

        try:
            elapsed = (now_dt - datetime.fromisoformat(candidate["started_at"])).total_seconds()
        except Exception:
            elapsed = 0

        if elapsed < MOVEMENT_CONFIRMATION_SECONDS:
            return None

        # Ten minutes stable: confirm and generate the enterprise event.
        state[key] = current
        pending.pop(key, None)
        _save_json(MOVEMENT_STATE_FILE, state)
        _save_json(MOVEMENT_PENDING_FILE, pending)

        event = {
            "time": current["last_seen"],
            "type": "CAMERA NVR MOVEMENT",
            "severity": "CRITICAL",
            "camera": current["camera"],
            "ip": current["ip"],
            "previous_nvr": previous.get("nvr"),
            "previous_channel": previous.get("channel"),
            "current_nvr": current["nvr"],
            "current_channel": current.get("channel"),
            "confirmation_seconds": MOVEMENT_CONFIRMATION_SECONDS,
            "details": (
                f"Camera remained on {current['nvr']} CH-{current.get('channel')} for "
                f"10 minutes. Previous assignment: {previous.get('nvr')} CH-{previous.get('channel')}."
            ),
        }
        history = _load_json(MOVEMENT_FILE, [])
        history.append(event)
        _save_json(MOVEMENT_FILE, history[-2000:])

    add_alert(
        "CAMERA NVR MOVEMENT",
        "CRITICAL",
        f"Camera moved NVR - {current['camera']}",
        event["details"],
    )
    print("\n" + "=" * 72)
    print("🚨 CAMERA NVR MOVEMENT CONFIRMED AFTER 10 MINUTES")
    print("Camera   :", current["camera"])
    print("Previous :", previous.get("nvr"), "CH", previous.get("channel"))
    print("Current  :", current["nvr"], "CH", current.get("channel"))
    print("IP       :", current["ip"])
    print("Time     :", current["last_seen"])
    print("=" * 72)
    try:
        send_camera_migration_email(
            camera=current["camera"],
            ip=current["ip"],
            old_nvr=previous.get("nvr", "-"),
            old_channel=previous.get("channel", "-"),
            new_nvr=current["nvr"],
            new_channel=current.get("channel", "-"),
            event_time=current["last_seen"],
        )
    except Exception as exc:
        print("[ENTERPRISE] Migration email error:", exc)
    return event


def get_camera_movement_history(limit: int = 500):
    history = _load_json(MOVEMENT_FILE, [])
    return list(reversed(history[-limit:]))


def camera_movement_summary():
    history = _load_json(MOVEMENT_FILE, [])
    pending = _load_json(MOVEMENT_PENDING_FILE, {})
    by_camera = {}
    for item in history:
        by_camera[item.get("camera", "Unknown")] = by_camera.get(item.get("camera", "Unknown"), 0) + 1
    pending_items = []
    now_dt = datetime.now()
    for key, item in pending.items():
        try:
            elapsed = max(0, int((now_dt - datetime.fromisoformat(item.get("started_at"))).total_seconds()))
        except Exception:
            elapsed = 0
        pending_items.append({
            "identity": key,
            "camera": item.get("candidate", {}).get("camera", "Unknown"),
            "nvr": item.get("candidate", {}).get("nvr", "Unknown"),
            "channel": item.get("candidate", {}).get("channel"),
            "elapsed_seconds": elapsed,
            "remaining_seconds": max(0, MOVEMENT_CONFIRMATION_SECONDS - elapsed),
            "confirmation_seconds": MOVEMENT_CONFIRMATION_SECONDS,
        })
    return {
        "total_movements": len(history),
        "unique_cameras": len(by_camera),
        "by_camera": by_camera,
        "pending_movements": len(pending_items),
        "pending": pending_items,
        "confirmation_seconds": MOVEMENT_CONFIRMATION_SECONDS,
    }


def _find_nvr(name: str):
    for nvr in NVRS:
        if nvr["name"].lower() == str(name).lower():
            return nvr
    return None


def _find_channel_xml(nvr: dict, channel_id: int):
    r = _nvr_request(nvr, "GET", f"/ISAPI/ContentMgmt/InputProxy/channels/{int(channel_id)}")
    if r.ok and r.text.strip():
        return r.text
    r = _nvr_request(nvr, "GET", "/ISAPI/ContentMgmt/InputProxy/channels")
    if not r.ok:
        raise RuntimeError(f"Unable to read channel configuration: HTTP {r.status_code}")
    root = ET.fromstring(r.text)
    for node in root.findall(".//{*}InputProxyChannel"):
        id_node = node.find("{*}id")
        if id_node is not None and id_node.text and int(id_node.text) == int(channel_id):
            return ET.tostring(node, encoding="unicode")
    raise RuntimeError(f"Channel {channel_id} not found")


def update_camera(nvr_name: str, channel_id: int, changes: Dict[str, Any]):
    nvr = _find_nvr(nvr_name)
    if not nvr:
        raise ValueError(f"NVR not found: {nvr_name}")
    xml = _find_channel_xml(nvr, channel_id)
    root = ET.fromstring(xml)

    if "name" in changes and changes["name"] is not None:
        node = root.find("{*}name")
        if node is None:
            node = ET.SubElement(root, "name")
        node.text = str(changes["name"]).strip()

    if "ip" in changes and changes["ip"] is not None:
        ip_nodes = root.findall(".//{*}ipAddress")
        if ip_nodes:
            ip_nodes[0].text = str(changes["ip"]).strip()
        else:
            descriptor = root.find("{*}sourceInputPortDescriptor")
            if descriptor is None:
                descriptor = ET.SubElement(root, "sourceInputPortDescriptor")
            ip_node = ET.SubElement(descriptor, "ipAddress")
            ip_node.text = str(changes["ip"]).strip()

    if "enabled" in changes and changes["enabled"] is not None:
        value = "true" if bool(changes["enabled"]) else "false"
        nodes = root.findall(".//{*}enabled") or root.findall(".//{*}enable")
        if nodes:
            nodes[0].text = value
        else:
            node = ET.SubElement(root, "enabled")
            node.text = value

    body = ET.tostring(root, encoding="unicode")
    r = _nvr_request(nvr, "PUT", f"/ISAPI/ContentMgmt/InputProxy/channels/{int(channel_id)}", body)
    if not r.ok:
        raise RuntimeError(f"NVR rejected camera update: HTTP {r.status_code} {r.text[:300]}")
    add_alert(
        "CAMERA SETTINGS",
        "INFO",
        f"Camera settings changed - {changes.get('name') or channel_id}",
        f"{nvr_name} CH-{channel_id}: {', '.join(changes.keys())}",
    )
    return {"success": True, "nvr": nvr_name, "channel": channel_id, "changes": changes, "status": r.status_code}
