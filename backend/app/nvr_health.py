"""Live NVR health telemetry and alert generation."""
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.auth import HTTPDigestAuth

from .config import NVRS
from .alert_manager import add_alert

TIMEOUT = 5
POLL_SECONDS = 5
CPU_WARN = 75
CPU_CRITICAL = 90
MEM_WARN = 80
MEM_CRITICAL = 90
TEMP_WARN = 70
TEMP_CRITICAL = 80
DISK_WARN = 90
DISK_CRITICAL = 98
ALERT_COOLDOWN = 60

_lock = threading.RLock()
_cache = {}
_alert_state = {}
_started = False
_thread = None


def _lname(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _text(node, names, default=None):
    wanted = {str(n).lower() for n in names}
    for child in node.iter():
        if _lname(child.tag) in wanted and child.text:
            return child.text.strip()
    return default


def _float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _get(nvr, endpoint):
    try:
        r = requests.get(
            f"http://{nvr['ip']}:{nvr['port']}{endpoint}",
            auth=HTTPDigestAuth(nvr["username"], nvr["password"]),
            headers={"Accept": "application/xml"},
            timeout=TIMEOUT,
        )
        if r.ok and r.text:
            return r.text
    except requests.RequestException:
        pass
    return None


def _parse_status(xml_text):
    if not xml_text:
        return None
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    cpus = []
    for node in root.iter():
        if _lname(node.tag) == "cpu":
            value = _float(_text(node, ("cpuUtilization", "utilization")))
            if value is not None:
                cpus.append({
                    "description": _text(node, ("cpuDescription", "description"), "CPU"),
                    "usage": max(0, min(100, round(value, 1))),
                })

    memories = []
    for node in root.iter():
        if _lname(node.tag) == "memory":
            used = _float(_text(node, ("memoryUsage", "usage")))
            available = _float(_text(node, ("memoryAvailable", "available")))
            if used is not None:
                total = used + available if available is not None else None
                memories.append({
                    "description": _text(node, ("memoryDescription", "description"), "Memory"),
                    "used_mb": round(used, 2),
                    "available_mb": round(available, 2) if available is not None else None,
                    "usage_percent": round((used / total) * 100, 1) if total and total > 0 else None,
                })

    temps = []
    for node in root.iter():
        if _lname(node.tag) == "temperature":
            value = _float(_text(node, ("temperature",)))
            if value is not None:
                temps.append({
                    "description": _text(node, ("tempSensorDescription", "description"), "Temperature"),
                    "celsius": round(value, 1),
                })

    uptime = _float(_text(root, ("deviceUpTime", "uptime")))
    current_time = _text(root, ("currentDeviceTime",))
    return {
        "cpus": cpus,
        "cpu_percent": round(sum(x["usage"] for x in cpus) / len(cpus), 1) if cpus else None,
        "memories": memories,
        "memory_percent": next((x["usage_percent"] for x in memories if x["usage_percent"] is not None), None),
        "temperatures": temps,
        "temperature_c": max((x["celsius"] for x in temps), default=None),
        "uptime_seconds": round(uptime) if uptime is not None else None,
        "device_time": current_time,
    }


def _alert_once(key, severity, title, description, active=True):
    now = time.time()
    state = _alert_state.get(key, {})
    if active:
        if state.get("active") and now - state.get("last", 0) < ALERT_COOLDOWN:
            return
        add_alert("NVR Health", severity, title, description)
        _alert_state[key] = {"active": True, "last": now}
    elif state.get("active"):
        add_alert("NVR Recovery", "INFO", f"Recovered: {title}", description)
        _alert_state[key] = {"active": False, "last": now}


def _collect(nvr):
    xml = _get(nvr, "/ISAPI/System/status")
    if not xml:
        return {
            "id": nvr["id"], "name": nvr["name"], "ip": nvr["ip"], "port": nvr["port"],
            "status": "OFFLINE", "cpu_percent": None, "memory_percent": None,
            "temperature_c": None, "uptime_seconds": None, "cpus": [], "memories": [], "temperatures": [],
            "error": "NVR unreachable or /ISAPI/System/status unavailable",
        }
    parsed = _parse_status(xml) or {}
    return {
        "id": nvr["id"], "name": nvr["name"], "ip": nvr["ip"], "port": nvr["port"],
        "status": "ONLINE", "error": None, **parsed,
    }


def refresh_health():
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(NVRS))) as executor:
        results = list(executor.map(_collect, NVRS))

    # Storage is already polled independently. We only use its current cache
    # when available so health polling remains fast.
    try:
        from .storage_monitor import get_storage
        storage = {x["name"]: x for x in get_storage(force=False)}
    except Exception:
        storage = {}

    for item in results:
        name = item["name"]
        if item["status"] == "OFFLINE":
            _alert_once(f"{name}:offline", "CRITICAL", f"{name} Offline", f"{name} at {item['ip']}:{item['port']} is unreachable.")
            continue
        _alert_once(f"{name}:offline", "INFO", f"{name} Offline", f"{name} is reachable again.", active=False)

        cpu = item.get("cpu_percent")
        _alert_once(f"{name}:cpu", "CRITICAL", f"{name} High CPU", f"CPU usage is {cpu}% (critical threshold {CPU_CRITICAL}%).", active=cpu is not None and cpu >= CPU_CRITICAL)
        if cpu is not None and cpu < CPU_CRITICAL:
            _alert_once(f"{name}:cpu", "WARNING", f"{name} High CPU", f"CPU usage is {cpu}% (warning threshold {CPU_WARN}%).", active=cpu >= CPU_WARN)

        mem = item.get("memory_percent")
        _alert_once(f"{name}:memory", "CRITICAL", f"{name} High Memory", f"Memory usage is {mem}% (critical threshold {MEM_CRITICAL}%).", active=mem is not None and mem >= MEM_CRITICAL)
        if mem is not None and mem < MEM_CRITICAL:
            _alert_once(f"{name}:memory", "WARNING", f"{name} High Memory", f"Memory usage is {mem}% (warning threshold {MEM_WARN}%).", active=mem >= MEM_WARN)

        temp = item.get("temperature_c")
        _alert_once(f"{name}:temp", "CRITICAL", f"{name} High Temperature", f"Device temperature is {temp}°C.", active=temp is not None and temp >= TEMP_CRITICAL)
        if temp is not None and temp < TEMP_CRITICAL:
            _alert_once(f"{name}:temp", "WARNING", f"{name} High Temperature", f"Device temperature is {temp}°C.", active=temp >= TEMP_WARN)

        disk = storage.get(name)
        if disk and disk.get("status") == "ONLINE":
            pct = disk.get("used_percent")
            if pct is not None:
                _alert_once(f"{name}:disk", "CRITICAL", f"{name} Storage Critical", f"Storage usage is {pct}%.", active=pct >= DISK_CRITICAL)
                if pct < DISK_CRITICAL:
                    _alert_once(f"{name}:disk", "WARNING", f"{name} Storage High", f"Storage usage is {pct}%.", active=pct >= DISK_WARN)
            bad = [d for d in disk.get("hdds", []) if str(d.get("status", "")).lower() not in {"ok", "normal", "healthy"}]
            _alert_once(f"{name}:hdd", "CRITICAL", f"{name} HDD Issue", f"{len(bad)} HDD(s) report a non-healthy status.", active=bool(bad))
        elif disk and disk.get("status") == "ONLINE" and disk.get("error"):
            _alert_once(f"{name}:storage", "WARNING", f"{name} Storage Telemetry Issue", disk.get("error"), active=True)
        else:
            _alert_once(f"{name}:storage", "WARNING", f"{name} Storage Unavailable", "Storage telemetry could not be read.", active=bool(disk and disk.get("status") == "ONLINE"))

    with _lock:
        _cache.clear()
        _cache.update({x["name"]: x for x in results})
        return list(_cache.values())


def get_health(force=False):
    if force or not _cache:
        return refresh_health()
    with _lock:
        return list(_cache.values())


def _loop():
    while True:
        try:
            refresh_health()
        except Exception as exc:
            print(f"NVR health monitor error: {exc}")
        time.sleep(POLL_SECONDS)


def start_health_monitor():
    global _started, _thread
    if _started:
        return
    _started = True
    _thread = threading.Thread(target=_loop, name="nvr-health-monitor", daemon=True)
    _thread.start()
