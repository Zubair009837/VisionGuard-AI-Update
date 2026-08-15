from datetime import datetime
import time
import json
from pathlib import Path
from collections import defaultdict

from .config import (
    ALERT_DELAY_SECONDS,
    ENABLE_DUPLICATE_PROTECTION
)

from .email_service import (
    send_offline_email,
    send_recovery_email,
    send_nvr_offline_email,
    send_nvr_recovery_email
)


# ==========================================================
# VisionGuard AI - Alert Manager
# ==========================================================
#
# CAMERA OFFLINE:
#   5 continuous minutes before alert
#
# NVR OFFLINE:
#   Existing ALERT_DELAY_SECONDS
#
# RECORDING:
#   Handled separately by recording_monitor.py
#
# ==========================================================


# ==========================================================
# Camera Offline Configuration
# ==========================================================

CAMERA_OFFLINE_DELAY_SECONDS = 5 * 60


# ==========================================================
# Runtime Camera State
# ==========================================================

camera_status = {}

offline_since = {}

alert_sent = {}


# ==========================================================
# Runtime NVR State
# ==========================================================

nvr_status = {}

nvr_offline_since = {}

nvr_alert_sent = {}

nvr_camera_cache = defaultdict(dict)


# ==========================================================
# History
# ==========================================================

HISTORY_FILE = (
    Path(__file__).parent /
    "alert_history.json"
)


# ==========================================================
# Time
# ==========================================================

def current_time():

    return datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


# ==========================================================
# Camera History
# ==========================================================

def save_history(
    camera,
    status
):

    history = []

    if HISTORY_FILE.exists():

        try:

            with open(
                HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                history = json.load(f)

        except Exception:

            history = []

    history.append({

        "camera":
            camera.get("name", ""),

        "nvr":
            camera.get("nvr", ""),

        "ip":
            camera.get("ip", ""),

        "status":
            status,

        "time":
            current_time()

    })

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                indent=4
            )

    except Exception as e:

        print(
            f"History Save Error: {e}"
        )


# ==========================================================
# NVR History
# ==========================================================

def save_nvr_history(
    nvr,
    status,
    affected_count
):

    history = []

    if HISTORY_FILE.exists():

        try:

            with open(
                HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                history = json.load(f)

        except Exception:

            history = []

    history.append({

        "type":
            "NVR",

        "nvr":
            nvr,

        "status":
            status,

        "affected_cameras":
            affected_count,

        "time":
            current_time()

    })

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                indent=4
            )

    except Exception as e:

        print(
            f"NVR History Save Error: {e}"
        )


# ==========================================================
# Register Camera
# ==========================================================

def register_nvr_camera(
    camera
):

    nvr = camera.get(
        "nvr",
        ""
    )

    camera_id = str(
        camera.get(
            "id",
            ""
        )
    )

    if not nvr or not camera_id:

        return

    nvr_camera_cache[nvr][
        camera_id
    ] = dict(camera)


# ==========================================================
# Get NVR Cameras
# ==========================================================

def get_nvr_cameras(
    nvr
):

    return list(
        nvr_camera_cache.get(
            nvr,
            {}
        ).values()
    )


# ==========================================================
# PROCESS NVR
# ==========================================================

def process_nvr(
    nvr,
    status,
    cameras=None
):

    if not nvr:

        return

    # ------------------------------------------------------
    # Register supplied cameras
    # ------------------------------------------------------

    if cameras:

        for camera in cameras:

            register_nvr_camera(
                camera
            )

    # ------------------------------------------------------
    # Use cached inventory if no list supplied
    # ------------------------------------------------------

    affected_cameras = (
        cameras
        if cameras is not None
        else get_nvr_cameras(nvr)
    )

    affected_cameras = list(
        affected_cameras
    )

    # ======================================================
    # NVR OFFLINE
    # ======================================================

    if status == "Offline":

        # --------------------------------------------------
        # First detection
        # --------------------------------------------------

        if nvr not in nvr_status:

            nvr_status[nvr] = "Offline"

            nvr_offline_since[nvr] = time.time()

            print(
                f"🔴 NVR OFFLINE DETECTED | "
                f"{nvr} | "
                f"Cameras: {len(affected_cameras)}"
            )

            return

        # --------------------------------------------------
        # Already offline
        # --------------------------------------------------

        if nvr_status[nvr] == "Offline":

            elapsed = (
                time.time()
                -
                nvr_offline_since.get(
                    nvr,
                    time.time()
                )
            )

            # Existing NVR delay remains unchanged
            if elapsed < ALERT_DELAY_SECONDS:

                return

            # Duplicate protection
            if (
                ENABLE_DUPLICATE_PROTECTION
                and
                nvr_alert_sent.get(nvr)
            ):

                return

            # --------------------------------------------------
            # ONE NVR EMAIL
            # --------------------------------------------------

            success = send_nvr_offline_email(

                nvr=nvr,

                cameras=affected_cameras,

                event_time=current_time()

            )

            if success:

                save_nvr_history(

                    nvr,

                    "Offline",

                    len(affected_cameras)

                )

                nvr_alert_sent[nvr] = True

                print(
                    f"📧 NVR OFFLINE MAIL SENT | "
                    f"{nvr} | "
                    f"{len(affected_cameras)} cameras"
                )

            return

    # ======================================================
    # NVR ONLINE
    # ======================================================

    if status == "Online":

        previous = nvr_status.get(
            nvr
        )

        # --------------------------------------------------
        # Recovery
        # --------------------------------------------------

        if previous == "Offline":

            success = send_nvr_recovery_email(

                nvr=nvr,

                cameras=affected_cameras,

                event_time=current_time()

            )

            if success:

                save_nvr_history(

                    nvr,

                    "Recovered",

                    len(affected_cameras)

                )

                print(
                    f"📧 NVR RECOVERY MAIL SENT | "
                    f"{nvr} | "
                    f"{len(affected_cameras)} cameras"
                )

        # --------------------------------------------------
        # Reset state
        # --------------------------------------------------

        nvr_status[nvr] = "Online"

        nvr_offline_since.pop(
            nvr,
            None
        )

        nvr_alert_sent.pop(
            nvr,
            None
        )


# ==========================================================
# PROCESS CAMERA
# ==========================================================

def process_camera(
    camera
):

    nvr = camera.get(
        "nvr",
        ""
    )

    camera_id = str(
        camera.get(
            "id",
            ""
        )
    )

    key = (
        f"{nvr}_{camera_id}"
    )

    current = camera.get(
        "status",
        ""
    )

    # ------------------------------------------------------
    # Register camera
    # ------------------------------------------------------

    register_nvr_camera(
        camera
    )

    # ======================================================
    # Whole NVR is Offline
    #
    # Do not send individual camera emails.
    # ======================================================

    if (
        current == "Offline"
        and
        nvr_status.get(nvr) == "Offline"
    ):

        camera_status[key] = current

        if key not in offline_since:

            offline_since[key] = time.time()

        return

    # ======================================================
    # First observation
    # ======================================================

    if key not in camera_status:

        camera_status[key] = current

        if current == "Offline":

            offline_since[key] = time.time()

        return

    previous = camera_status[key]

    # ======================================================
    # CAMERA OFFLINE
    # ======================================================

    if current == "Offline":

        if key not in offline_since:

            offline_since[key] = time.time()

        elapsed = (
            time.time()
            -
            offline_since[key]
        )

        print(
            f"⚠️ CAMERA OFFLINE CHECK | "
            f"{camera.get('name', '')} | "
            f"NVR={nvr} | "
            f"offline={int(elapsed)}s / "
            f"{CAMERA_OFFLINE_DELAY_SECONDS}s"
        )

        # --------------------------------------------------
        # IMPORTANT:
        # Camera must remain offline continuously
        # for 5 minutes.
        # --------------------------------------------------

        if elapsed < CAMERA_OFFLINE_DELAY_SECONDS:

            camera_status[key] = current

            return

        # --------------------------------------------------
        # Duplicate protection
        # --------------------------------------------------

        if (
            ENABLE_DUPLICATE_PROTECTION
            and
            alert_sent.get(key)
        ):

            camera_status[key] = current

            return

        # --------------------------------------------------
        # SEND OFFLINE EMAIL
        # --------------------------------------------------

        success = send_offline_email(

            camera=camera.get(
                "name",
                ""
            ),

            nvr=nvr,

            ip=camera.get(
                "ip",
                ""
            ),

            event_time=current_time()

        )

        if success:

            save_history(
                camera,
                "Offline"
            )

            alert_sent[key] = True

            print(
                f"📧 CAMERA OFFLINE MAIL SENT | "
                f"{camera.get('name', '')} | "
                f"NVR={nvr} | "
                f"Offline={int(elapsed)}s"
            )

    # ======================================================
    # CAMERA ONLINE / RECOVERY
    # ======================================================

    elif current == "Online":

        if previous == "Offline":

            # ------------------------------------------------
            # IMPORTANT:
            #
            # Recovery email should ONLY be sent if an
            # actual offline alert was already sent.
            #
            # If camera was offline for only 2 or 3 minutes,
            # there was no alert -> no recovery email.
            # ------------------------------------------------

            was_alerted = alert_sent.get(
                key,
                False
            )

            if (
                nvr_status.get(nvr) != "Offline"
                and
                was_alerted
            ):

                success = send_recovery_email(

                    camera=camera.get(
                        "name",
                        ""
                    ),

                    nvr=nvr,

                    ip=camera.get(
                        "ip",
                        ""
                    ),

                    event_time=current_time()

                )

                if success:

                    save_history(
                        camera,
                        "Recovered"
                    )

                    print(
                        f"📧 CAMERA RECOVERY MAIL SENT | "
                        f"{camera.get('name', '')} | "
                        f"NVR={nvr}"
                    )

        # --------------------------------------------------
        # Reset offline state
        # --------------------------------------------------

        offline_since.pop(
            key,
            None
        )

        alert_sent.pop(
            key,
            None
        )

    # ------------------------------------------------------
    # Update status
    # ------------------------------------------------------

    camera_status[key] = current


# ==========================================================
# GENERIC ALERT
# ==========================================================

def add_alert(
    alert_type,
    severity,
    title,
    description
):

    history = []

    if HISTORY_FILE.exists():

        try:

            with open(
                HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                history = json.load(f)

        except Exception:

            history = []

    history.append({

        "type":
            alert_type,

        "severity":
            severity,

        "title":
            title,

        "description":
            description,

        "time":
            current_time()

    })

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                indent=4
            )

    except Exception as e:

        print(
            f"Generic Alert History Error: {e}"
        )

    print(
        f"[{severity}] {title}"
    )


# ==========================================================
# MODULE LOAD
# ==========================================================

print(
    "=" * 70
)

print(
    "✅ VisionGuard AI Alert Manager Loaded"
)

print(
    "📦 NVR Group Alert Protection Enabled"
)

print(
    "📧 NVR Offline = Existing Delay"
)

print(
    "📧 NVR Recovery = 1 Mail"
)

print(
    "📧 Camera Offline = 5 Minute Delay"
)

print(
    "📧 Camera Recovery = Only After Alert"
)

print(
    "📧 Individual Camera = Individual Mail"
)

print(
    "=" * 70
)