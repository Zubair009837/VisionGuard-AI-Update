# ==========================================================
# VisionGuard AI - Main FastAPI Application
# Tata 1mg - NVR Security Operations Center
# ==========================================================


# ==========================================================
# STANDARD LIBRARIES
# ==========================================================

import time

from typing import List


# ==========================================================
# VIDEO MONITOR
# ==========================================================

from .video_monitor import (
    start_video_monitor,
    rtsp_url,
)


# ==========================================================
# HIKVISION EVENT LISTENER
# ==========================================================

from .hikvision_event_listener import (
    start_listener,
)


# ==========================================================
# RECORDING MONITOR
# ==========================================================

from .recording_monitor import (
    start_recording_monitor,
    get_recording_loss_history,
    get_active_recording_losses,
)


# ==========================================================
# CAMERA ANGLE MONITOR
# ==========================================================

from .camera_angle_monitor import (
    start_camera_angle_monitor,
    stop_camera_angle_monitor,
    get_camera_angle_status,
    get_camera_angle_summary,
)


# ==========================================================
# FASTAPI
# ==========================================================

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
)


# ==========================================================
# CORS
# ==========================================================

from fastapi.middleware.cors import (
    CORSMiddleware
)


# ==========================================================
# RESPONSES
# ==========================================================

from fastapi.responses import (
    PlainTextResponse,
    StreamingResponse,
)


# ==========================================================
# DATABASE
# ==========================================================

from sqlalchemy.orm import Session

from .database import (
    Base,
    engine,
    get_db,
)


# ==========================================================
# SCHEMAS
# ==========================================================

from .schemas import (
    CameraCreate,
    CameraResponse,
)


# ==========================================================
# CRUD
# ==========================================================

from . import crud


# ==========================================================
# CONFIG
# ==========================================================

from .config import NVRS

from .storage_monitor import storage_snapshot
from .nvr_health import get_health, start_health_monitor
from .alert_manager import add_alert, HISTORY_FILE
from .enterprise_features import (
    nvr_users,
    get_camera_movement_history,
    camera_movement_summary,
    update_camera,
)


# ==========================================================
# REQUESTS
# ==========================================================

import requests

from requests.auth import HTTPDigestAuth


# ==========================================================
# OPENCV
# ==========================================================

import cv2


# ==========================================================
# APPLICATION
# ==========================================================

app = FastAPI(
    title="VisionGuard AI",
    version="3.4 Enterprise",
)


# ==========================================================
# DATABASE
# ==========================================================

Base.metadata.create_all(
    bind=engine
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# NVR STATUS
#
# Dashboard does NOT perform a live NVR scan.
# crud.py background monitor owns the cache.
# ==========================================================

def get_nvr_status():

    return crud.get_cached_nvr_status()


# ==========================================================
# STARTUP
# ==========================================================

@app.on_event("startup")
def startup():

    print("=" * 70)
    print("VisionGuard AI Starting...")
    print("=" * 70)

    # ------------------------------------------------------
    # CAMERA / NVR BACKGROUND DISCOVERY
    # ------------------------------------------------------

    try:

        start_health_monitor()
        print("✓ NVR Health/CPU Monitor Started")

        crud.start_background_monitor()

        print(
            "✓ NVR/Camera Background Monitor "
            "Started Successfully"
        )

    except Exception as e:

        print(
            f"✗ Camera Monitor Error: {e}"
        )

    # ------------------------------------------------------
    # NVR STATUS
    # ------------------------------------------------------

    try:

        status = crud.get_cached_nvr_status()

        online = sum(
            1
            for nvr in status
            if nvr.get("status") == "ONLINE"
        )

        print(
            f"✓ NVR Cache Ready "
            f"({online}/{len(NVRS)} online)"
        )

    except Exception as e:

        print(
            f"✗ NVR Status Cache Error: {e}"
        )

    # ------------------------------------------------------
    # VIDEO MONITOR
    # ------------------------------------------------------

    try:

        start_video_monitor()

        print(
            "✓ Video Monitor Started Successfully"
        )

    except Exception as e:

        print(
            f"✗ Video Monitor Error: {e}"
        )

    # ------------------------------------------------------
    # HIKVISION EVENT LISTENER
    # ------------------------------------------------------

    try:

        start_listener()

        print(
            "✓ Hikvision Event Listener "
            "Started Successfully"
        )

    except Exception as e:

        print(
            f"✗ Event Listener Error: {e}"
        )

    # ------------------------------------------------------
    # RECORDING LOSS MONITOR
    # ------------------------------------------------------

    try:

        start_recording_monitor()

        print(
            "✓ Recording Loss Monitor "
            "Started Successfully"
        )

    except Exception as e:

        print(
            f"✗ Recording Monitor Error: {e}"
        )

    # ------------------------------------------------------
    # CAMERA ANGLE MONITOR
    # ------------------------------------------------------

    try:

        print("📐 Starting Camera Angle Monitor...")
        start_camera_angle_monitor()

        print(
            "✓ Camera Angle Monitor Started Successfully | "
            "first scan runs immediately; subsequent scans use configured interval"
        )

    except Exception as e:

        print(
            f"✗ Camera Angle Monitor Error: {e}"
        )

    print("=" * 70)


# ==========================================================
# SHUTDOWN
# ==========================================================

@app.on_event("shutdown")
def shutdown():

    print("=" * 70)
    print("VisionGuard AI Shutting Down...")
    print("=" * 70)

    # ------------------------------------------------------
    # NVR / CAMERA BACKGROUND MONITOR
    # ------------------------------------------------------

    try:

        crud.stop_background_monitor()

        print(
            "✓ NVR/Camera Background Monitor Stopped"
        )

    except Exception as e:

        print(
            f"⚠️ Monitor Shutdown Error: {e}"
        )

    # ------------------------------------------------------
    # CAMERA ANGLE MONITOR
    # ------------------------------------------------------

    try:

        stop_camera_angle_monitor()

        print(
            "✓ Camera Angle Monitor Stopped"
        )

    except Exception as e:

        print(
            f"⚠️ Camera Angle Monitor "
            f"Shutdown Error: {e}"
        )


# ==========================================================
# FIND NVR FOR LIVE
# ==========================================================

def find_nvr_for_live(
    nvr_name: str
):

    target = str(
        nvr_name
    ).strip().lower()

    for nvr in NVRS:

        if (
            str(
                nvr.get("name", "")
            ).strip().lower()
            == target
        ):

            return nvr

    return None


# ==========================================================
# LIVE MJPEG GENERATOR
# ==========================================================

def live_mjpeg_generator(
    nvr,
    channel_id: int
):

    stream_id = (
        int(channel_id) * 100 + 1
    )

    url = rtsp_url(
        nvr,
        stream_id
    )

    cap = None

    try:

        print(
            f"[LIVE] Opening RTSP: "
            f"{nvr['name']} "
            f"Channel {channel_id}"
        )

        cap = cv2.VideoCapture(
            url,
            cv2.CAP_FFMPEG
        )

        if not cap.isOpened():

            print(
                f"[LIVE] RTSP open failed: "
                f"{nvr['name']} "
                f"channel {channel_id}"
            )

            return

        try:

            cap.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

        except Exception:

            pass

        while True:

            ok, frame = cap.read()

            if (
                not ok
                or frame is None
            ):

                print(
                    f"[LIVE] Stream ended: "
                    f"{nvr['name']} "
                    f"channel {channel_id}"
                )

                break

            ok, encoded = cv2.imencode(
                ".jpg",
                frame,
                [
                    int(
                        cv2.IMWRITE_JPEG_QUALITY
                    ),
                    80,
                ],
            )

            if not ok:

                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + encoded.tobytes()
                + b"\r\n"
            )

            time.sleep(
                0.03
            )

    except GeneratorExit:

        return

    except Exception as exc:

        print(
            f"[LIVE] Stream error "
            f"{nvr['name']} "
            f"channel {channel_id}: "
            f"{exc}"
        )

    finally:

        if cap is not None:

            cap.release()

        print(
            f"[LIVE] Stream closed: "
            f"{nvr['name']} "
            f"channel {channel_id}"
        )


# ==========================================================
# LIVE STREAM
# ==========================================================

@app.get(
    "/live/stream/{nvr_name}/{channel_id}"
)
def live_stream(
    nvr_name: str,
    channel_id: int
):

    nvr = find_nvr_for_live(
        nvr_name
    )

    if nvr is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"NVR '{nvr_name}' "
                f"not found"
            ),
        )

    if channel_id < 1:

        raise HTTPException(
            status_code=400,
            detail=(
                "Channel ID must be "
                "greater than 0"
            ),
        )

    return StreamingResponse(
        live_mjpeg_generator(
            nvr,
            channel_id
        ),
        media_type=(
            "multipart/"
            "x-mixed-replace;"
            " boundary=frame"
        ),
        headers={
            "Cache-Control":
                "no-cache, no-store, "
                "must-revalidate",

            "Pragma":
                "no-cache",

            "Expires":
                "0",

            "X-Accel-Buffering":
                "no",
        },
    )


# ==========================================================
# LIVE STREAM TEST
# ==========================================================

@app.get(
    "/live/test/{nvr_name}/{channel_id}"
)
def live_test(
    nvr_name: str,
    channel_id: int
):

    nvr = find_nvr_for_live(
        nvr_name
    )

    if nvr is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"NVR '{nvr_name}' "
                f"not found"
            ),
        )

    if channel_id < 1:

        raise HTTPException(
            status_code=400,
            detail=(
                "Channel ID must be "
                "greater than 0"
            ),
        )

    stream_id = (
        int(channel_id) * 100 + 1
    )

    return {
        "success": True,
        "nvr": nvr["name"],
        "nvr_ip": nvr["ip"],
        "channel": channel_id,
        "stream_id": stream_id,
        "rtsp_port": 554,
        "stream_endpoint": (
            f"/live/stream/"
            f"{nvr['name']}/"
            f"{channel_id}"
        ),
    }


# ==========================================================
# HOME
# ==========================================================

@app.get("/")
def home():

    return {
        "message":
            "VisionGuard AI Backend Running"
    }


# ==========================================================
# HEALTH
# ==========================================================

@app.get("/health")
def health():

    return {
        "status":
            "UP"
    }


# ==========================================================
# DASHBOARD
#
# IMPORTANT:
# This endpoint ONLY reads the cache.
# It NEVER scans the NVRs.
# ==========================================================

@app.get("/dashboard")
def dashboard():

    snapshot = (
        crud.get_dashboard_snapshot()
    )

    return snapshot


# ==========================================================
# CAMERAS
#
# Python 3.8 compatible.
# ==========================================================

@app.get(
    "/cameras",
    response_model=List[CameraResponse],
)
def get_cameras():

    return crud.get_cached_cameras(
        online_only=True
    )


# ==========================================================
# CREATE CAMERA
# ==========================================================

@app.post(
    "/cameras",
    response_model=CameraResponse,
)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db)
):

    created = crud.create_camera(
        db,
        camera
    )

    return created


# ==========================================================
# NVR STATUS
# ==========================================================

@app.get("/nvr/status")
def nvr_status():

    return crud.get_cached_nvr_status()


# ==========================================================
# STORAGE
#
# Reads real HDD telemetry from every configured NVR.
# ==========================================================

@app.get("/storage")
def storage():

    return storage_snapshot(force=False)


@app.get("/storage/refresh")
def storage_refresh():

    return storage_snapshot(force=True)


@app.get("/nvr/health")
def nvr_health(force: bool = False):
    return {"data": get_health(force=force), "configured_nvrs": len(NVRS)}


@app.get("/analytics/summary")
def analytics_summary():
    """Live aggregate telemetry for the Analytics dashboard."""
    import json
    from .ip_conflict_checker import get_conflict_count, get_conflict_ips
    from .recording_monitor import get_statistics
    try:
        snapshot = crud.get_dashboard_snapshot()
        alert_data = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                alert_data = json.load(f)[-100:]
        recording_stats = get_statistics()
        try:
            storage_data = storage_snapshot(force=False).get("data", [])
        except Exception:
            storage_data = []
        movement = camera_movement_summary()
        try:
            angle = get_camera_angle_summary()
        except Exception:
            angle = {}
        return {
            "overview": {
                "total_cameras": snapshot.get("total", 0),
                "online_cameras": snapshot.get("online", 0),
                "offline_cameras": snapshot.get("offline", 0),
                "total_nvrs": snapshot.get("total_nvr", len(NVRS)),
                "online_nvrs": snapshot.get("online_nvr", 0),
                "offline_nvrs": snapshot.get("offline_nvr", 0),
                "cache_ready": snapshot.get("cache_ready", False),
                "last_update": snapshot.get("last_update"),
            },
            "nvr_health": snapshot.get("nvr_status", []),
            "recent_alerts": list(reversed(alert_data[-30:])),
            "recording": {
                "active_losses": recording_stats.get("active_losses", 0),
                "history": recording_stats.get("history", 0),
                "pending": recording_stats.get("pending", 0),
                "threshold_seconds": recording_stats.get("threshold", 300),
                "running": recording_stats.get("running", False),
            },
            "storage": storage_data,
            "movement": movement,
            "angle": angle,
            "ip_conflicts": {"count": get_conflict_count(), "ips": get_conflict_ips()},
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analytics aggregation failed: {exc}")


@app.get("/alerts")
def alerts():
    try:
        if HISTORY_FILE.exists():
            import json
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data[-500:]
    except Exception as exc:
        print(f"Alert history read error: {exc}")
    return []


# ----------------------------------------------------------
# NVR SETTINGS / ISAPI
# ----------------------------------------------------------

def _get_nvr(nvr_id: int):
    for nvr in NVRS:
        if int(nvr.get("id")) == int(nvr_id):
            return nvr
    raise HTTPException(status_code=404, detail="NVR not found")


def _nvr_request(nvr, method, endpoint, body=None):
    if not endpoint.startswith("/ISAPI/"):
        raise HTTPException(status_code=400, detail="Only /ISAPI/* endpoints are allowed")
    if any(x in endpoint.lower() for x in ("factoryreset", "updatefirmware", "configurationdata")):
        raise HTTPException(status_code=403, detail="This destructive endpoint is disabled from the web UI")
    try:
        r = requests.request(
            method,
            f"http://{nvr['ip']}:{nvr['port']}{endpoint}",
            auth=HTTPDigestAuth(nvr["username"], nvr["password"]),
            data=body.encode("utf-8") if isinstance(body, str) else body,
            headers={"Accept": "application/xml", "Content-Type": "application/xml"},
            timeout=10,
        )
        if not r.ok:
            raise HTTPException(status_code=r.status_code, detail=r.text[:1000] or "NVR rejected request")
        return {"status": r.status_code, "content_type": r.headers.get("content-type", ""), "body": r.text}
    except HTTPException:
        raise
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"NVR connection failed: {exc}")


@app.get("/nvr/{nvr_id}/settings")
def nvr_settings(nvr_id: int, section: str = "device", endpoint: str = ""):
    nvr = _get_nvr(nvr_id)
    endpoints = {
        "device": "/ISAPI/System/deviceInfo",
        "time": "/ISAPI/System/time",
        "network": "/ISAPI/System/Network/interfaces",
        "capabilities": "/ISAPI/System/capabilities",
    }
    if section == "advanced":
        endpoint = endpoint or "/ISAPI/System/deviceInfo"
        if not endpoint.startswith("/ISAPI/"):
            raise HTTPException(status_code=400, detail="Only /ISAPI/* endpoints are allowed")
    else:
        endpoint = endpoints.get(section)
    if not endpoint:
        raise HTTPException(status_code=400, detail="Unsupported settings section")
    return _nvr_request(nvr, "GET", endpoint)


@app.put("/nvr/{nvr_id}/settings")
def update_nvr_settings(nvr_id: int, payload: dict):
    nvr = _get_nvr(nvr_id)
    endpoint = str(payload.get("endpoint", ""))
    xml = payload.get("xml", "")
    if not xml:
        raise HTTPException(status_code=400, detail="XML payload is required")
    result = _nvr_request(nvr, "PUT", endpoint, xml)
    add_alert("NVR Settings", "INFO", f"{nvr['name']} Settings Changed", f"Updated {endpoint}")
    return result


@app.put("/nvr/bulk/settings")
def update_bulk_nvr_settings(payload: dict):
    """Apply one prepared ISAPI XML payload per selected NVR.

    The frontend prepares each NVR's XML independently so unique values such as
    IP addresses are never accidentally copied from one recorder to another.
    """
    items = payload.get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="No NVRs selected")

    results = []
    for item in items:
        try:
            nvr_id = int(item.get("nvr_id"))
            endpoint = str(item.get("endpoint", ""))
            xml = item.get("xml", "")
            nvr = _get_nvr(nvr_id)
            if not xml:
                raise ValueError("XML payload is empty")
            result = _nvr_request(nvr, "PUT", endpoint, xml)
            results.append({
                "nvr_id": nvr_id,
                "nvr": nvr.get("name"),
                "success": True,
                "status": result.get("status"),
                "endpoint": endpoint,
            })
            add_alert(
                "NVR SETTINGS",
                "INFO",
                f"{nvr['name']} Settings Changed",
                f"Bulk update applied to {endpoint}",
            )
        except Exception as exc:
            if isinstance(exc, HTTPException):
                detail = exc.detail
            else:
                detail = str(exc)
            results.append({
                "nvr_id": item.get("nvr_id"),
                "nvr": item.get("name", f"NVR-{item.get('nvr_id', '?')}"),
                "success": False,
                "error": detail,
                "endpoint": item.get("endpoint", ""),
            })

    succeeded = sum(1 for r in results if r.get("success"))
    return {
        "success": succeeded == len(results),
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }


@app.post("/nvr/{nvr_id}/reboot")
def reboot_nvr(nvr_id: int):
    nvr = _get_nvr(nvr_id)
    result = _nvr_request(nvr, "PUT", "/ISAPI/System/reboot", "")
    add_alert("NVR Settings", "WARNING", f"{nvr['name']} Reboot Requested", "NVR reboot command was sent from Settings.")
    return result


# ==========================================================
# NVR RAW
# ==========================================================

@app.get(
    "/nvr/raw",
    response_class=PlainTextResponse,
)
def nvr_raw():

    output = ""

    for nvr in NVRS:

        output += (
            "\n========== "
            f"{nvr['name']}"
            " ==========\n"
        )

        try:

            response = requests.get(
                f"http://"
                f"{nvr['ip']}:"
                f"{nvr['port']}"
                "/ISAPI/ContentMgmt/"
                "InputProxy/channels",
                auth=HTTPDigestAuth(
                    nvr["username"],
                    nvr["password"],
                ),
                timeout=10,
            )

            output += response.text

        except Exception as e:

            output += str(e)

    return output


# ==========================================================
# ENTERPRISE NVR USERS
# ==========================================================

@app.get("/nvr/users")
def get_all_nvr_users():
    return {"configured_nvrs": len(NVRS), "nvrs": nvr_users()}


@app.put("/nvr/users/bulk-update")
def bulk_update_nvr_users(payload: dict):
    """Apply safe user account changes to selected NVR accounts.
    Supported changes: enabled and userLevel/role. Password changes are intentionally excluded.
    """
    items = payload.get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="No users selected")
    results = []
    for item in items:
        try:
            nvr = _get_nvr(int(item.get("nvr_id")))
            user_id = str(item.get("user_id"))
            if not user_id:
                raise ValueError("User ID is required")
            response = _nvr_request(nvr, "GET", f"/ISAPI/Security/users/{user_id}")
            root = __import__("xml.etree.ElementTree", fromlist=["ElementTree"]).fromstring(response["body"])
            changes = item.get("changes") or {}
            for key in ("enabled", "enable"):
                if key in changes:
                    nodes = root.findall(".//{*}" + key)
                    if nodes:
                        nodes[0].text = "true" if bool(changes[key]) else "false"
                    else:
                        import xml.etree.ElementTree as ET
                        node = ET.SubElement(root, key); node.text = "true" if bool(changes[key]) else "false"
            if "role" in changes or "userLevel" in changes:
                raw_role = str(changes.get("role", changes.get("userLevel"))).strip().lower()
                role_map = {
                    "admin": "Administrator",
                    "administrator": "Administrator",
                    "operator": "Operator",
                    "viewer": "Viewer",
                }
                value = role_map.get(raw_role, str(changes.get("role", changes.get("userLevel"))))
                nodes = root.findall(".//{*}userLevel") or root.findall(".//{*}role")
                if nodes: nodes[0].text = value
            import xml.etree.ElementTree as ET
            body = ET.tostring(root, encoding="unicode")
            result = _nvr_request(nvr, "PUT", f"/ISAPI/Security/users/{user_id}", body)
            add_alert("NVR USER SETTINGS", "INFO", f"User settings changed - {nvr['name']}", f"User ID {user_id}")
            results.append({"success": True, "nvr_id": nvr["id"], "nvr": nvr["name"], "user_id": user_id, "status": result.get("status")})
        except Exception as exc:
            results.append({"success": False, "nvr_id": item.get("nvr_id"), "nvr": item.get("nvr"), "user_id": item.get("user_id"), "error": str(exc)})
    ok = sum(1 for x in results if x["success"])
    return {"success": ok == len(results), "total": len(results), "succeeded": ok, "failed": len(results)-ok, "results": results}


@app.get("/nvr/users/summary")
def get_nvr_user_summary():
    data = nvr_users()
    return {
        "total_users": sum(int(item.get("user_count", 0)) for item in data),
        "online_nvrs": sum(1 for item in data if item.get("status") == "ONLINE"),
        "configured_nvrs": len(NVRS),
        "nvrs": data,
    }


# ==========================================================
# ENTERPRISE CAMERA MANAGEMENT
# ==========================================================

@app.post("/cameras/bulk-update")
def bulk_update_cameras(payload: dict):
    cameras = payload.get("cameras") or []
    changes = payload.get("changes") or {}
    if not cameras:
        raise HTTPException(status_code=400, detail="No cameras selected")
    if not changes:
        raise HTTPException(status_code=400, detail="No changes supplied")
    results = []
    errors = []
    for item in cameras:
        try:
            result = update_camera(str(item.get("nvr")), int(item.get("id")), changes)
            results.append(result)
        except Exception as exc:
            errors.append({"nvr": item.get("nvr"), "id": item.get("id"), "error": str(exc)})
    return {"success": not errors, "updated": len(results), "failed": len(errors), "results": results, "errors": errors}


@app.post("/cameras/{nvr_name}/{channel_id}/settings")
def update_single_camera(nvr_name: str, channel_id: int, payload: dict):
    changes = payload.get("changes") or payload
    try:
        return update_camera(nvr_name, channel_id, changes)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ==========================================================
# CAMERA NVR MOVEMENT HISTORY
# ==========================================================

@app.get("/camera-movements")
def camera_movements(limit: int = 500):
    return {"history": get_camera_movement_history(limit), "summary": camera_movement_summary()}


# ==========================================================
# RECORDING LOSS
# ==========================================================

@app.get("/recording-loss/statistics")
def recording_loss_statistics():
    from .recording_monitor import get_statistics
    return get_statistics()


@app.get("/ip-conflicts")
def ip_conflicts():
    from .ip_conflict_checker import get_conflict_count, get_conflict_ips, active_conflicts
    return {"count": get_conflict_count(), "ips": get_conflict_ips(), "active": list(active_conflicts)}


@app.get("/recording-loss")
def recording_loss():

    return {
        "active":
            get_active_recording_losses(),

        "history":
            get_recording_loss_history(),
    }


# ==========================================================
# CAMERA ANGLE STATUS
# ==========================================================

@app.get(
    "/camera-angle/status"
)
def camera_angle_status():

    return get_camera_angle_status()


# ==========================================================
# CAMERA ANGLE SUMMARY
# ==========================================================

@app.get(
    "/camera-angle/summary"
)
def camera_angle_summary():

    return get_camera_angle_summary()


# ==========================================================
# APPLICATION INFO
# ==========================================================

@app.get("/api/info")
def application_info():

    snapshot = (
        crud.get_dashboard_snapshot()
    )

    return {

        "application":
            "VisionGuard AI",

        "version":
            "3.2 Enterprise",

        "status":
            "running",

        "nvrs":
            snapshot.get(
                "online_nvr",
                0
            ),

        "configured_nvrs":
            len(NVRS),

        "features": [

            "Video Loss Monitoring",

            "Video Recovery Detection",

            "Hikvision Event Listener",

            "Recording Loss Detection",

            "Recording Recovery Detection",

            "Live RTSP Streaming",

            "Camera Management",

            "NVR Status Monitoring",

            "Recording Loss History",

            "Background Camera Discovery",

            "Camera Status Cache",

            "Camera Angle Change Detection",
        ],
    }


# ==========================================================
# END OF MAIN.PY
# ==========================================================