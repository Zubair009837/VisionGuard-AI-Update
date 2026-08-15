# ==========================================================
# VisionGuard AI Enterprise Recording Engine v2
# Enterprise Recording Monitor
#
# RECORDING LOSS ALERT:
#   10 minutes continuous recording gap
#
# CHECK:
#   Every 30 seconds
#
# VERIFICATION:
#   Additional 30 second re-check
#
# ==========================================================

import threading
import time
import uuid
import requests
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta
from requests.auth import HTTPDigestAuth


# ==========================================================
# Import Config
# ==========================================================

try:

    from .config import NVRS

except Exception:

    NVRS = []


# ==========================================================
# Alert Manager
# ==========================================================

try:

    from .alert_manager import add_alert

except Exception:

    def add_alert(*args, **kwargs):

        print(
            "[ALERT]",
            args,
            kwargs
        )


# ==========================================================
# Email Service
# ==========================================================

try:

    from .email_service import (
        send_recording_loss_email,
        send_recording_recovery_email,
    )

except Exception:

    def send_recording_loss_email(
        *args,
        **kwargs
    ):

        pass

    def send_recording_recovery_email(
        *args,
        **kwargs
    ):

        pass


# ==========================================================
# Enterprise Recording Settings
# ==========================================================

CHECK_INTERVAL = 30

RECHECK_DELAY = 30

# ----------------------------------------------------------
# IMPORTANT
#
# Recording must be missing for 10 minutes before alert.
# ----------------------------------------------------------

RECORDING_GAP_THRESHOLD = 10 * 60

SEARCH_WINDOW = 1200

REQUEST_TIMEOUT = 15


# ==========================================================
# Runtime
# ==========================================================

RUNNING = False

THREAD = None

LOCK = threading.Lock()

ACTIVE_LOSSES = {}

LOSS_HISTORY = []

TRACK_CACHE = {}

PENDING_VERIFICATION = {}


# ==========================================================
# Date Helpers
# ==========================================================

def now():

    return datetime.now()


def format_time(
    dt=None
):

    if dt is None:

        dt = now()

    return dt.strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


def format_duration(
    seconds
):

    seconds = int(
        max(
            0,
            seconds
        )
    )

    h, r = divmod(
        seconds,
        3600
    )

    m, s = divmod(
        r,
        60
    )

    if h:

        return (
            f"{h}h "
            f"{m}m "
            f"{s}s"
        )

    if m:

        return (
            f"{m}m "
            f"{s}s"
        )

    return f"{s}s"


# ==========================================================
# NVR Helper
# ==========================================================

def nvr_value(
    nvr,
    *keys,
    default=None
):

    for key in keys:

        if isinstance(
            nvr,
            dict
        ):

            if key in nvr:

                return nvr[key]

        elif hasattr(
            nvr,
            key
        ):

            return getattr(
                nvr,
                key
            )

    return default


# ==========================================================
# Hikvision Request
# ==========================================================

def hik_request(
    nvr,
    endpoint,
    method="GET",
    body=None,
    quiet=False,
):

    host = nvr_value(
        nvr,
        "ip",
        "host",
        default=""
    )

    port = nvr_value(
        nvr,
        "port",
        default=80
    )

    user = nvr_value(
        nvr,
        "username",
        "user",
        default=""
    )

    password = nvr_value(
        nvr,
        "password",
        "pass",
        default=""
    )

    if not host:

        return None

    url = (
        f"http://"
        f"{host}:"
        f"{port}"
        f"{endpoint}"
    )

    try:

        response = requests.request(

            method,

            url,

            auth=HTTPDigestAuth(
                user,
                password
            ),

            data=body,

            headers={
                "Content-Type":
                    "application/xml"
            },

            timeout=REQUEST_TIMEOUT

        )

        if response.status_code != 200:

            if not quiet:

                print(
                    f"[HTTP "
                    f"{response.status_code}]",
                    url
                )

            return None

        return response.text

    except Exception as exc:

        if not quiet:

            print(
                "[HIKVISION ERROR]",
                exc
            )

        return None


# ==========================================================
# Camera Discovery
# ==========================================================

def get_cameras(
    nvr
):

    xml = hik_request(

        nvr,

        "/ISAPI/ContentMgmt/InputProxy/channels"

    )

    if not xml:

        return []

    cameras = []

    try:

        root = ET.fromstring(
            xml
        )

        for item in root.findall(
            ".//{*}InputProxyChannel"
        ):

            node_id = item.find(
                "{*}id"
            )

            node_name = item.find(
                "{*}name"
            )

            if node_id is None:

                continue

            channel = int(
                node_id.text
            )

            if (
                node_name is not None
                and
                node_name.text
            ):

                name = (
                    node_name.text.strip()
                )

            else:

                name = (
                    f"Camera "
                    f"{channel}"
                )

            cameras.append({

                "id":
                    channel,

                "name":
                    name

            })

    except Exception as exc:

        print(
            "[Camera Parse Error]",
            exc
        )

    return cameras


# ==========================================================
# Track Candidates
# ==========================================================

def get_track_candidates(
    nvr,
    channel
):

    host = nvr_value(
        nvr,
        "ip",
        "host",
        default=""
    )

    cache_key = (
        f"{host}:{channel}"
    )

    result = []

    cached = TRACK_CACHE.get(
        cache_key
    )

    if cached:

        result.append(
            cached
        )

    result.extend([

        channel * 100 + 1,

        channel * 100 + 2,

        channel,

        channel + 100,

        channel + 200,

        channel + 1000

    ])

    unique = []

    for value in result:

        try:

            value = int(
                value
            )

        except Exception:

            continue

        if value not in unique:

            unique.append(
                value
            )

    return unique


# ==========================================================
# Build Recording Search XML
# ==========================================================

def build_search_xml(
    search_id,
    track_id,
    start_time,
    end_time
):

    start = start_time.strftime(
        "%Y-%m-%dT%H:%M:%S+05:30"
    )

    end = end_time.strftime(
        "%Y-%m-%dT%H:%M:%S+05:30"
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CMSearchDescription>

<searchID>{search_id}</searchID>

<trackList>
<trackID>{track_id}</trackID>
</trackList>

<timeSpanList>

<timeSpan>

<startTime>{start}</startTime>

<endTime>{end}</endTime>

</timeSpan>

</timeSpanList>

<maxResults>1000</maxResults>

<searchResultPosition>0</searchResultPosition>

<metadataList>

<metadataDescriptor>
//recordType.meta.std-cgi.com
</metadataDescriptor>

</metadataList>

</CMSearchDescription>
"""


# ==========================================================
# Parse Recording Result
# ==========================================================

def parse_recordings(
    xml
):

    recordings = []

    if not xml:

        return recordings

    try:

        root = ET.fromstring(
            xml
        )

    except Exception:

        return recordings

    for item in root.findall(
        ".//{*}searchMatchItem"
    ):

        s = item.find(
            ".//{*}startTime"
        )

        e = item.find(
            ".//{*}endTime"
        )

        if (
            s is None
            or
            e is None
        ):

            continue

        try:

            start = datetime.fromisoformat(
                s.text.replace(
                    "Z",
                    "+00:00"
                )
            ).replace(
                tzinfo=None
            )

            end = datetime.fromisoformat(
                e.text.replace(
                    "Z",
                    "+00:00"
                )
            ).replace(
                tzinfo=None
            )

            recordings.append({

                "start":
                    start,

                "end":
                    end

            })

        except Exception:

            pass

    recordings.sort(
        key=lambda x:
            x["start"]
    )

    return recordings


# ==========================================================
# Recording Search
# ==========================================================

def search_recording(
    nvr,
    channel,
    start_time,
    end_time
):

    host = nvr_value(
        nvr,
        "ip",
        "host",
        default=""
    )

    cache_key = (
        f"{host}:{channel}"
    )

    tracks = get_track_candidates(
        nvr,
        channel
    )

    for track in tracks:

        xml = build_search_xml(

            str(
                uuid.uuid4()
            ),

            track,

            start_time,

            end_time

        )

        result = hik_request(

            nvr,

            "/ISAPI/ContentMgmt/search",

            method="POST",

            body=xml,

            quiet=True

        )

        if not result:

            continue

        lower = result.lower()

        if (
            "invalid track id"
            in lower
        ):

            continue

        clips = parse_recordings(
            result
        )

        if clips:

            TRACK_CACHE[
                cache_key
            ] = track

            return clips

        if (
            "<responsestatus>true"
            in lower
        ):

            TRACK_CACHE[
                cache_key
            ] = track

            return []

    return []


# ==========================================================
# Recording Gap Detection
# ==========================================================

def find_gap(
    recordings,
    current_time
):

    if not recordings:

        return None

    last_end = (
        recordings[0]["end"]
    )

    for clip in recordings[1:]:

        gap = (

            clip["start"]

            -

            last_end

        ).total_seconds()

        if (
            gap
            >=
            RECORDING_GAP_THRESHOLD
        ):

            return {

                "start":
                    last_end,

                "end":
                    clip["start"],

                "duration":
                    int(gap)

            }

        last_end = max(

            last_end,

            clip["end"]

        )

    tail_gap = (

        current_time

        -

        last_end

    ).total_seconds()

    if (
        tail_gap
        >=
        RECORDING_GAP_THRESHOLD
    ):

        return {

            "start":
                last_end,

            "end":
                current_time,

            "duration":
                int(tail_gap)

        }

    return None


# ==========================================================
# Recording Verification
# ==========================================================

def verify_gap(
    nvr,
    camera,
    gap
):

    key = (
        f"{nvr_value(nvr, 'name')}:"
        f"{camera['id']}"
    )

    current = now()

    pending = PENDING_VERIFICATION.get(
        key
    )

    # ------------------------------------------------------
    # First detection
    # ------------------------------------------------------

    if pending is None:

        PENDING_VERIFICATION[key] = {

            "first_seen":
                current,

            "gap":
                gap

        }

        print(
            f"⚠️ RECORDING GAP DETECTED | "
            f"{key} | "
            f"Gap={format_duration(gap['duration'])} | "
            f"Threshold="
            f"{format_duration(RECORDING_GAP_THRESHOLD)}"
        )

        return None

    # ------------------------------------------------------
    # Recording gap must still be >= 10 minutes
    # ------------------------------------------------------

    if (
        gap["duration"]
        <
        RECORDING_GAP_THRESHOLD
    ):

        return None

    # ------------------------------------------------------
    # Double verification
    # ------------------------------------------------------

    elapsed = (
        current
        -
        pending["first_seen"]
    ).total_seconds()

    if elapsed < RECHECK_DELAY:

        print(
            f"⏳ RECORDING GAP VERIFYING | "
            f"{key} | "
            f"Recheck in "
            f"{int(RECHECK_DELAY - elapsed)}s"
        )

        return None

    del PENDING_VERIFICATION[
        key
    ]

    return gap


# ==========================================================
# Clear Verification
# ==========================================================

def clear_verification(
    nvr,
    camera
):

    key = (

        f"{nvr_value(nvr, 'name')}:"

        f"{camera['id']}"

    )

    PENDING_VERIFICATION.pop(
        key,
        None
    )


# ==========================================================
# Recording Loss Alert
# ==========================================================

def send_recording_loss_alert(
    nvr_name,
    nvr_ip,
    camera_name,
    camera_id,
    gap
):

    key = (
        f"{nvr_name}:"
        f"{camera_id}"
    )

    # ------------------------------------------------------
    # Duplicate protection
    # ------------------------------------------------------

    if key in ACTIVE_LOSSES:

        return

    ACTIVE_LOSSES[key] = {

        "nvr":
            nvr_name,

        "nvr_ip":
            nvr_ip,

        "camera":
            camera_name,

        "camera_id":
            camera_id,

        "loss_start":
            gap["start"],

        "loss_end":
            gap["end"],

        "status":
            "RECORDING LOST",

        "created":
            now()

    }

    print(
        "\n" +
        "=" * 70
    )

    print(
        "[CRITICAL] RECORDING LOSS"
    )

    print(
        "=" * 70
    )

    print(
        "NVR      :",
        nvr_name
    )

    print(
        "Camera   :",
        camera_name
    )

    print(
        "Channel  :",
        camera_id
    )

    print(
        "IP       :",
        nvr_ip
    )

    print(
        "From     :",
        format_time(
            gap["start"]
        )
    )

    print(
        "To       :",
        format_time(
            gap["end"]
        )
    )

    print(
        "Duration :",
        format_duration(
            gap["duration"]
        )
    )

    print(
        "Threshold:",
        format_duration(
            RECORDING_GAP_THRESHOLD
        )
    )

    print(
        "=" * 70
    )

    # ------------------------------------------------------
    # Dashboard / Alert History
    # ------------------------------------------------------

    try:

        add_alert(

            alert_type=
                "RECORDING LOSS",

            severity=
                "CRITICAL",

            title=
                f"Recording Loss - "
                f"{camera_name}",

            description=(
                f"NVR : {nvr_name}\n"
                f"Camera : {camera_name}\n"
                f"IP : {nvr_ip}\n"
                f"Recording Missing\n"
                f"Duration : "
                f"{format_duration(gap['duration'])}"
            )

        )

    except Exception as exc:

        print(
            "[ALERT HISTORY ERROR]",
            exc
        )

    # ------------------------------------------------------
    # Email
    # ------------------------------------------------------

    try:

        send_recording_loss_email(

            camera=
                camera_name,

            nvr=
                nvr_name,

            ip=
                nvr_ip,

            loss_from=
                format_time(
                    gap["start"]
                ),

            loss_to=
                format_time(
                    gap["end"]
                ),

            duration=
                format_duration(
                    gap["duration"]
                )

        )

    except Exception as exc:

        print(
            "EMAIL ERROR :",
            exc
        )


# ==========================================================
# Recording Recovery Alert
# ==========================================================

def send_recording_recovery_alert(
    key
):

    if key not in ACTIVE_LOSSES:

        return

    event = ACTIVE_LOSSES[
        key
    ]

    restore_time = now()

    duration = int(

        (
            restore_time

            -

            event["loss_start"]

        ).total_seconds()

    )

    print(
        "\n" +
        "=" * 70
    )

    print(
        "[RECOVERY]"
    )

    print(
        "=" * 70
    )

    print(
        "NVR      :",
        event["nvr"]
    )

    print(
        "Camera   :",
        event["camera"]
    )

    print(
        "IP       :",
        event["nvr_ip"]
    )

    print(
        "Restored :",
        format_time(
            restore_time
        )
    )

    print(
        "Duration :",
        format_duration(
            duration
        )
    )

    print(
        "=" * 70
    )

    try:

        send_recording_recovery_email(

            camera=
                event["camera"],

            nvr=
                event["nvr"],

            ip=
                event["nvr_ip"],

            loss_from=
                format_time(
                    event["loss_start"]
                ),

            loss_to=
                format_time(
                    event["loss_end"]
                ),

            restored_at=
                format_time(
                    restore_time
                ),

            duration=
                format_duration(
                    duration
                )

        )

    except Exception as exc:

        print(
            "Recovery Email Error :",
            exc
        )

    LOSS_HISTORY.append({

        **event,

        "restored":
            restore_time,

        "duration":
            duration

    })

    del ACTIVE_LOSSES[
        key
    ]


# ==========================================================
# Check Single Camera
# ==========================================================

def check_camera(
    nvr,
    camera
):

    nvr_name = nvr_value(

        nvr,

        "name",

        default="NVR"

    )

    nvr_ip = nvr_value(

        nvr,

        "ip",

        default=""

    )

    current = now()

    start = (

        current
        -
        timedelta(
            seconds=SEARCH_WINDOW
        )

    )

    recordings = search_recording(

        nvr,

        camera["id"],

        start,

        current

    )

    gap = find_gap(

        recordings,

        current

    )

    key = (
        f"{nvr_name}:"
        f"{camera['id']}"
    )

    # ======================================================
    # RECORDING OK
    # ======================================================

    if gap is None:

        clear_verification(

            nvr,

            camera

        )

        if key in ACTIVE_LOSSES:

            send_recording_recovery_alert(
                key
            )

        return

    # ======================================================
    # RECORDING LOSS FOUND
    # ======================================================

    verified = verify_gap(

        nvr,

        camera,

        gap

    )

    if verified is None:

        return

    # ======================================================
    # SEND ALERT
    # ======================================================

    send_recording_loss_alert(

        nvr_name,

        nvr_ip,

        camera["name"],

        camera["id"],

        verified

    )


# ==========================================================
# Scan One NVR
# ==========================================================

def scan_nvr(
    nvr
):

    nvr_name = nvr_value(

        nvr,

        "name",

        default="NVR"

    )

    print(
        f"[RECORDING] "
        f"Scanning {nvr_name}"
    )

    cameras = get_cameras(
        nvr
    )

    if not cameras:

        print(
            f"[RECORDING] "
            f"{nvr_name} : "
            f"No Cameras Found"
        )

        return

    print(
        f"[RECORDING] "
        f"{nvr_name}: "
        f"{len(cameras)} Cameras"
    )

    for camera in cameras:

        try:

            check_camera(

                nvr,

                camera

            )

        except Exception as exc:

            print(

                "[RECORDING]",

                camera.get(
                    "name",
                    camera.get(
                        "id",
                        ""
                    )
                ),

                exc

            )


# ==========================================================
# Scan All NVRs
# ==========================================================

def scan_all():

    for nvr in NVRS:

        try:

            scan_nvr(
                nvr
            )

        except Exception as exc:

            print(
                "[SCAN ERROR]",
                exc
            )


# ==========================================================
# Monitor Loop
# ==========================================================

def monitor_loop():

    global RUNNING

    print(
        "=" * 70
    )

    print(
        "[RECORDING] "
        "Enterprise Recording Monitor Started"
    )

    print(
        f"Threshold : "
        f"{RECORDING_GAP_THRESHOLD}s "
        f"("
        f"{format_duration(RECORDING_GAP_THRESHOLD)}"
        f")"
    )

    print(
        f"Recheck   : "
        f"{RECHECK_DELAY}s"
    )

    print(
        f"Interval  : "
        f"{CHECK_INTERVAL}s"
    )

    print(
        "=" * 70
    )

    while RUNNING:

        try:

            scan_all()

        except Exception as exc:

            print(
                "[MONITOR]",
                exc
            )

        time.sleep(
            CHECK_INTERVAL
        )


# ==========================================================
# Start Monitor
# ==========================================================

def start_recording_monitor():

    global THREAD

    global RUNNING

    if (
        THREAD
        and
        THREAD.is_alive()
    ):

        print(
            "[RECORDING] "
            "Already Running"
        )

        return

    RUNNING = True

    THREAD = threading.Thread(

        target=
            monitor_loop,

        daemon=True,

        name=
            "VisionGuardRecording"

    )

    THREAD.start()

    print(
        "Recording Loss Monitor "
        "Started Successfully"
    )


# ==========================================================
# Stop Monitor
# ==========================================================

def stop_recording_monitor():

    global RUNNING

    RUNNING = False

    print(
        "Recording Monitor Stopped"
    )


# ==========================================================
# APIs
# ==========================================================

def get_active_recording_losses():

    return list(
        ACTIVE_LOSSES.values()
    )


def get_recording_loss_history():

    return list(
        reversed(
            LOSS_HISTORY
        )
    )


def clear_recording_history():

    ACTIVE_LOSSES.clear()

    LOSS_HISTORY.clear()

    PENDING_VERIFICATION.clear()

    print(
        "[RECORDING] "
        "History Cleared"
    )


def get_statistics():

    return {

        "running":
            RUNNING,

        "active_losses":
            len(
                ACTIVE_LOSSES
            ),

        "history":
            len(
                LOSS_HISTORY
            ),

        "pending":
            len(
                PENDING_VERIFICATION
            ),

        "cached_tracks":
            len(
                TRACK_CACHE
            ),

        "interval":
            CHECK_INTERVAL,

        "threshold":
            RECORDING_GAP_THRESHOLD,

        "threshold_minutes":
            RECORDING_GAP_THRESHOLD / 60,

        "recheck":
            RECHECK_DELAY,

    }


# ==========================================================
# Manual Scan
# ==========================================================

def run_recording_scan():

    print(
        "[RECORDING] "
        "Manual Scan Started"
    )

    scan_all()

    print(
        "[RECORDING] "
        "Manual Scan Completed"
    )


# ==========================================================
# Module Loaded
# ==========================================================

print(
    "=" * 70
)

print(
    "VisionGuard AI "
    "Enterprise Recording Engine v2 Loaded"
)

print(
    "Recording Loss Threshold : 10 Minutes"
)

print(
    "Double Verification      : Enabled"
)

print(
    "Duplicate Protection     : Enabled"
)

print(
    "Recovery Detection       : Enabled"
)

print(
    "False Recording Filter   : Enabled"
)

print(
    "=" * 70
)