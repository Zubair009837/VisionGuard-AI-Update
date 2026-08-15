# ==========================================================
# VisionGuard AI - CACHE BASED NVR / CAMERA DISCOVERY
# ==========================================================

import threading
import time

from concurrent.futures import (
    ThreadPoolExecutor
)

import requests
import xml.etree.ElementTree as ET

from requests.auth import HTTPDigestAuth

from sqlalchemy.orm import Session

from .models import Camera
from .schemas import CameraCreate
from .config import NVRS

from .device_info import (
    fetch_device_info
)

from .device_registry import (
    register_device
)

from .identity_checker import (
    check_identity
)

from .alert_manager import (
    process_camera,
    process_nvr
)

from .ip_conflict_checker import (
    check_ip_conflicts,
    print_conflicts
)

from .enterprise_features import track_camera_assignment


# ==========================================================
# CONFIGURATION
# ==========================================================

SCAN_INTERVAL_SECONDS = 10

NVR_TIMEOUT_SECONDS = 5

XML_TIMEOUT_SECONDS = 10

MAX_NVR_WORKERS = max(
    1,
    len(NVRS)
)


# ==========================================================
# CACHE
# ==========================================================

_CACHE_LOCK = threading.RLock()

_CAMERA_CACHE = {}

_NVR_STATUS_CACHE = {}

_CACHE_READY = False

_CACHE_LAST_UPDATE = None


# ==========================================================
# BACKGROUND THREAD
# ==========================================================

_MONITOR_THREAD = None

_MONITOR_STOP_EVENT = (
    threading.Event()
)


# ==========================================================
# CACHE KEY
# ==========================================================

def _key(
    nvr_name,
    camera_id
):

    return (
        str(nvr_name),
        int(camera_id)
    )


# ==========================================================
# INITIALIZE CACHE
# ==========================================================

def _init_cache():

    with _CACHE_LOCK:

        for nvr in NVRS:

            _NVR_STATUS_CACHE.setdefault(
                nvr["name"],
                {
                    "name":
                        nvr["name"],

                    "ip":
                        nvr["ip"],

                    "port":
                        nvr["port"],

                    "status":
                        "UNKNOWN",

                    "camera_count":
                        0,
                }
            )


# ==========================================================
# SET NVR STATUS
# ==========================================================

def _set_nvr_status(
    nvr,
    status,
    camera_count=None
):

    global _CACHE_LAST_UPDATE

    with _CACHE_LOCK:

        if camera_count is None:

            camera_count = sum(
                1
                for c
                in _CAMERA_CACHE.values()
                if c.get("nvr")
                == nvr["name"]
            )

        _NVR_STATUS_CACHE[
            nvr["name"]
        ] = {

            "name":
                nvr["name"],

            "ip":
                nvr["ip"],

            "port":
                nvr["port"],

            "status":
                status,

            "camera_count":
                int(
                    camera_count
                ),
        }

        _CACHE_LAST_UPDATE = (
            time.time()
        )


# ==========================================================
# REMOVE NVR CAMERAS
# ==========================================================

def _remove_nvr(
    nvr_name
):

    with _CACHE_LOCK:

        for key in list(
            _CAMERA_CACHE
        ):

            if key[0] == nvr_name:

                del _CAMERA_CACHE[
                    key
                ]


# ==========================================================
# REPLACE NVR CAMERAS
# ==========================================================

def _replace_nvr(
    nvr_name,
    cameras
):

    with _CACHE_LOCK:

        for key in list(
            _CAMERA_CACHE
        ):

            if key[0] == nvr_name:

                del _CAMERA_CACHE[
                    key
                ]

        for camera in cameras:

            _CAMERA_CACHE[
                _key(
                    nvr_name,
                    camera["id"]
                )
            ] = dict(
                camera
            )


# ==========================================================
# FETCH XML
# ==========================================================

def fetch_xml(
    url,
    username,
    password,
    timeout=XML_TIMEOUT_SECONDS
):

    """
    Fetch Hikvision XML with HTTP Digest authentication.
    """

    try:

        response = requests.get(
            url,
            auth=HTTPDigestAuth(
                username,
                password
            ),
            timeout=timeout,
        )

        response.raise_for_status()

        if not response.text.strip():

            return None

        return ET.fromstring(
            response.text
        )

    except Exception as e:

        print(
            f"❌ XML Fetch Error | "
            f"{url} | {e}"
        )

        return None


# ==========================================================
# COMPATIBLE PAGINATED XML FETCH
# ==========================================================

def fetch_xml_compatible(
    base_url,
    username,
    password,
    timeout=XML_TIMEOUT_SECONDS
):

    """
    Try multiple Hikvision pagination formats
    and finally fall back to the plain endpoint.
    """

    urls = [

        (
            f"{base_url}"
            "?startPosition=0"
            "&maxResults=1000"
        ),

        (
            f"{base_url}"
            "?startPosition=1"
            "&maxResults=1000"
        ),

        base_url,
    ]

    for url in urls:

        root = fetch_xml(
            url,
            username,
            password,
            timeout
        )

        if root is not None:

            return root

    return None


# ==========================================================
# NVR ONLINE CHECK
# ==========================================================

def is_nvr_online(
    nvr
):

    try:

        response = requests.get(
            f"http://"
            f"{nvr['ip']}:"
            f"{nvr['port']}",

            auth=HTTPDigestAuth(
                nvr["username"],
                nvr["password"]
            ),

            timeout=NVR_TIMEOUT_SECONDS,
        )

        print(
            f"   {nvr['name']} "
            f"HTTP {response.status_code}"
        )

        return True

    except Exception as e:

        print(
            f"   {nvr['name']} "
            f"unreachable: {e}"
        )

        return False


# ==========================================================
# PARSE CHANNELS
# ==========================================================

def parse_channels(
    root
):

    result = {}

    if root is None:

        return result

    for channel in root.findall(
        ".//{*}InputProxyChannel"
    ):

        node = channel.find(
            "{*}id"
        )

        if (
            node is None
            or not node.text
        ):

            continue

        try:

            cid = int(
                node.text.strip()
            )

        except Exception:

            continue

        name = (
            f"Camera {cid}"
        )

        name_node = (
            channel.find(
                "{*}name"
            )
        )

        if (
            name_node is not None
            and name_node.text
        ):

            name = (
                name_node.text.strip()
            )

        # Hikvision firmware can place
        # ipAddress either directly under
        # InputProxyChannel or inside
        # sourceInputPortDescriptor.

        ip = ""

        ip_node = channel.find(
            ".//{*}ipAddress"
        )

        if (
            ip_node is not None
            and ip_node.text
        ):

            ip = (
                ip_node.text.strip()
            )

        result[
            cid
        ] = {

            "name":
                name,

            "ip":
                ip,
        }

    return result


# ==========================================================
# PARSE STATUS
# ==========================================================

def parse_status(
    root
):

    result = {}

    if root is None:

        return result

    for channel in root.findall(
        ".//{*}InputProxyChannelStatus"
    ):

        node = channel.find(
            "{*}id"
        )

        if (
            node is None
            or not node.text
        ):

            continue

        try:

            cid = int(
                node.text.strip()
            )

        except Exception:

            continue

        online = channel.find(
            "{*}online"
        )

        online_text = ""

        if (
            online is not None
            and online.text
        ):

            online_text = (
                online.text
                .strip()
                .lower()
            )

        result[
            cid
        ] = (
            "Online"
            if online_text == "true"
            else "Offline"
        )

    return result


# ==========================================================
# SCAN ONE NVR
# ==========================================================

def scan_nvr(
    nvr
):

    name = nvr["name"]

    print(
        f"\n🔍 SCAN "
        f"{name} | "
        f"{nvr['ip']}:"
        f"{nvr['port']}"
    )


    # ======================================================
    # NVR ONLINE CHECK
    # ======================================================

    if not is_nvr_online(
        nvr
    ):

        _set_nvr_status(
            nvr,
            "OFFLINE",
            0
        )

        _remove_nvr(
            name
        )

        try:

            process_nvr(
                name,
                "Offline",
                []
            )

        except Exception as e:

            print(
                f"⚠️ NVR Alert Error | "
                f"{name} | {e}"
            )

        print(
            f"🔴 {name} OFFLINE - "
            f"cameras removed from cache"
        )

        return


    # ======================================================
    # HIKVISION CHANNEL URL
    # ======================================================

    channels_url = (
        f"http://"
        f"{nvr['ip']}:"
        f"{nvr['port']}"
        "/ISAPI/ContentMgmt/"
        "InputProxy/channels"
    )


    # ======================================================
    # HIKVISION STATUS URL
    # ======================================================

    status_url = (
        f"http://"
        f"{nvr['ip']}:"
        f"{nvr['port']}"
        "/ISAPI/ContentMgmt/"
        "InputProxy/channels/status"
    )


    # ======================================================
    # CHANNEL DISCOVERY
    # ======================================================

    channels_root = (
        fetch_xml_compatible(
            channels_url,
            nvr["username"],
            nvr["password"]
        )
    )

    if channels_root is None:

        print(
            f"⚠️ {name} "
            f"channel API failed - "
            f"old cache preserved"
        )

        _set_nvr_status(
            nvr,
            "ONLINE"
        )

        return


    # ======================================================
    # STATUS DISCOVERY
    # ======================================================

    status_root = (
        fetch_xml_compatible(
            status_url,
            nvr["username"],
            nvr["password"]
        )
    )


    # ======================================================
    # PARSE
    # ======================================================

    channels = parse_channels(
        channels_root
    )

    statuses = parse_status(
        status_root
    )


    print(
        f"📡 {name} discovery | "
        f"channels={len(channels)} | "
        f"status_records={len(statuses)}"
    )


    # ======================================================
    # NO CHANNELS
    # ======================================================

    if not channels:

        print(
            f"⚠️ {name} is ONLINE "
            f"but no InputProxyChannel "
            f"records were parsed."
        )

        _set_nvr_status(
            nvr,
            "ONLINE",
            0
        )

        return


    # ======================================================
    # DEVICE INFO
    # ======================================================

    try:

        info = fetch_device_info(
            nvr["ip"],
            nvr["port"],
            nvr["username"],
            nvr["password"]
        ) or {}

    except Exception as e:

        print(
            f"⚠️ Device info error | "
            f"{name} | {e}"
        )

        info = {}


    # ======================================================
    # BUILD CAMERA CACHE
    # ======================================================

    cameras = []


    for cid in sorted(
        channels
    ):

        # --------------------------------------------------
        # Read old cache safely.
        # --------------------------------------------------

        with _CACHE_LOCK:

            old = _CAMERA_CACHE.get(
                _key(
                    name,
                    cid
                )
            )

            old = (
                dict(old)
                if old
                else None
            )


        # --------------------------------------------------
        # Camera status.
        #
        # If current status API contains the channel,
        # use it.
        #
        # If status API does not contain it, preserve old
        # status when available.
        # Otherwise mark Offline.
        # --------------------------------------------------

        if cid in statuses:

            camera_status = (
                statuses[cid]
            )

        elif old:

            camera_status = (
                old.get(
                    "status",
                    "Offline"
                )
            )

        else:

            camera_status = (
                "Offline"
            )


        camera = {

            "id":
                cid,

            "name":
                channels[cid][
                    "name"
                ],

            "ip":
                channels[cid][
                    "ip"
                ],

            "status":
                camera_status,

            "nvr":
                name,

            "serial":
                info.get(
                    "serial",
                    ""
                ),

            "model":
                info.get(
                    "model",
                    ""
                ),

            "firmware":
                info.get(
                    "firmware",
                    ""
                ),

            "mac":
                info.get(
                    "mac",
                    ""
                ),
        }


        # ==================================================
        # DEVICE REGISTRY
        # ==================================================

        try:

            track_camera_assignment(
                camera
            )

        except Exception as e:

            print(
                f"⚠️ Camera Movement Tracking Error | "
                f"{name} | {e}"
            )

        try:

            register_device(
                camera
            )

        except Exception as e:

            print(
                f"⚠️ Registry Error | "
                f"{name} | {e}"
            )


        # ==================================================
        # IDENTITY CHECK
        # ==================================================

        try:

            check_identity(
                camera
            )

        except Exception as e:

            print(
                f"⚠️ Identity Error | "
                f"{name} | {e}"
            )


        # ==================================================
        # CAMERA ALERT MANAGER
        # ==================================================

        try:

            process_camera(
                camera
            )

        except Exception as e:

            print(
                f"⚠️ Camera Alert Error | "
                f"{name} | {e}"
            )


        cameras.append(
            camera
        )


    # ======================================================
    # UPDATE CACHE
    # ======================================================

    _replace_nvr(
        name,
        cameras
    )


    _set_nvr_status(
        nvr,
        "ONLINE",
        len(cameras)
    )


    # ======================================================
    # NVR ALERT MANAGER
    # ======================================================

    try:

        process_nvr(
            name,
            "Online",
            cameras
        )

    except Exception as e:

        print(
            f"⚠️ NVR Online Alert Error | "
            f"{name} | {e}"
        )


    print(
        f"🟢 {name} ONLINE | "
        f"Cameras discovered: "
        f"{len(cameras)}"
    )


# ==========================================================
# SINGLE SCAN
# ==========================================================

def _scan_once():

    global _CACHE_READY

    _init_cache()


    # ======================================================
    # SCAN ALL NVRS IN PARALLEL
    # ======================================================

    with ThreadPoolExecutor(
        max_workers=MAX_NVR_WORKERS
    ) as executor:

        futures = [

            executor.submit(
                scan_nvr,
                nvr
            )

            for nvr in NVRS
        ]

        for future in futures:

            try:

                future.result()

            except Exception as e:

                print(
                    f"❌ NVR scan error: "
                    f"{e}"
                )


    # ======================================================
    # IP CONFLICT CHECK
    # ======================================================

    cameras = get_cached_cameras(
        online_only=True
    )

    if cameras:

        try:

            conflicts = (
                check_ip_conflicts(
                    cameras
                )
            )

            print_conflicts(
                conflicts
            )

        except Exception as e:

            print(
                f"⚠️ IP conflict "
                f"check error: {e}"
            )


    # ======================================================
    # CACHE READY
    # ======================================================

    _CACHE_READY = True


    # ======================================================
    # DASHBOARD SUMMARY
    # ======================================================

    snapshot = (
        get_dashboard_snapshot()
    )


    print(
        f"📊 CACHE: "
        f"NVR "
        f"{snapshot['online_nvr']}/"
        f"{snapshot['total_nvr']} online | "
        f"Cameras "
        f"{snapshot['total']} | "
        f"Online "
        f"{snapshot['online']} | "
        f"Offline "
        f"{snapshot['offline']}"
    )


# ==========================================================
# MONITOR LOOP
# ==========================================================

def _monitor_loop():

    print(
        f"✅ Background NVR/Camera "
        f"monitor started | "
        f"interval="
        f"{SCAN_INTERVAL_SECONDS}s"
    )


    # ------------------------------------------------------
    # Initial scan
    # ------------------------------------------------------

    try:

        _scan_once()

    except Exception as e:

        print(
            f"❌ Initial scan error: "
            f"{e}"
        )


    # ------------------------------------------------------
    # Continuous scans
    # ------------------------------------------------------

    while not _MONITOR_STOP_EVENT.wait(
        SCAN_INTERVAL_SECONDS
    ):

        try:

            _scan_once()

        except Exception as e:

            print(
                f"❌ Background scan error: "
                f"{e}"
            )


# ==========================================================
# START BACKGROUND MONITOR
# ==========================================================

def start_background_monitor():

    global _MONITOR_THREAD

    _init_cache()


    if (
        _MONITOR_THREAD is not None
        and
        _MONITOR_THREAD.is_alive()
    ):

        return


    _MONITOR_STOP_EVENT.clear()


    _MONITOR_THREAD = (
        threading.Thread(
            target=_monitor_loop,
            name=(
                "VisionGuard-"
                "NVR-Camera-Monitor"
            ),
            daemon=True,
        )
    )


    _MONITOR_THREAD.start()


# ==========================================================
# STOP BACKGROUND MONITOR
# ==========================================================

def stop_background_monitor():

    global _MONITOR_THREAD

    _MONITOR_STOP_EVENT.set()


    if (
        _MONITOR_THREAD is not None
        and
        _MONITOR_THREAD.is_alive()
    ):

        _MONITOR_THREAD.join(
            timeout=3
        )


    _MONITOR_THREAD = None


# ==========================================================
# GET NVR CACHE
# ==========================================================

def get_cached_nvr_status():

    _init_cache()

    with _CACHE_LOCK:

        result = []

        for nvr in NVRS:

            cached = (
                _NVR_STATUS_CACHE[
                    nvr["name"]
                ]
            )

            result.append({

                "name":
                    nvr["name"],

                "ip":
                    nvr["ip"],

                "port":
                    nvr["port"],

                "status":
                    cached.get(
                        "status",
                        "UNKNOWN"
                    ),

                "camera_count":
                    cached.get(
                        "camera_count",
                        0
                    ),
            })

        return result


# ==========================================================
# GET CAMERA CACHE
# ==========================================================

def get_cached_cameras(
    online_only=True
):

    with _CACHE_LOCK:

        online_nvrs = {

            n["name"]

            for n
            in _NVR_STATUS_CACHE.values()

            if n.get(
                "status"
            )
            == "ONLINE"
        }


        result = []


        for camera in (
            _CAMERA_CACHE.values()
        ):

            # ------------------------------------------------
            # online_only currently means:
            # only cameras belonging to ONLINE NVRs.
            #
            # Camera's own Online/Offline status is preserved.
            # ------------------------------------------------

            if (
                online_only
                and
                camera.get(
                    "nvr"
                )
                not in online_nvrs
            ):

                continue


            result.append(
                dict(
                    camera
                )
            )


    result.sort(
        key=lambda c: (
            str(
                c.get(
                    "nvr",
                    ""
                )
            ),

            int(
                c.get(
                    "id",
                    0
                )
            )
        )
    )


    return result


# ==========================================================
# DASHBOARD SNAPSHOT
# ==========================================================

def get_dashboard_snapshot():

    nvr_status = (
        get_cached_nvr_status()
    )


    online_nvrs = {

        n["name"]

        for n in nvr_status

        if n.get(
            "status"
        )
        == "ONLINE"
    }


    offline_nvrs = {

        n["name"]

        for n in nvr_status

        if n.get(
            "status"
        )
        == "OFFLINE"
    }


    cameras = (
        get_cached_cameras(
            online_only=True
        )
    )


    online = sum(

        1

        for c in cameras

        if str(
            c.get(
                "status",
                ""
            )
        ).lower()
        == "online"
    )


    offline = sum(

        1

        for c in cameras

        if str(
            c.get(
                "status",
                ""
            )
        ).lower()
        == "offline"
    )


    return {

        "total":
            len(cameras),

        "online":
            online,

        "offline":
            offline,

        "nvr":
            len(
                online_nvrs
            ),

        "total_nvr":
            len(NVRS),

        "online_nvr":
            len(
                online_nvrs
            ),

        "offline_nvr":
            len(
                offline_nvrs
            ),

        "nvr_status":
            nvr_status,

        "cache_ready":
            _CACHE_READY,

        "last_update":
            _CACHE_LAST_UPDATE,
    }


# ==========================================================
# GET CAMERAS
# ==========================================================

def get_cameras(
    db: Session = None
):

    return get_cached_cameras(
        online_only=True
    )


# ==========================================================
# CREATE CAMERA
# ==========================================================

def create_camera(
    db: Session,
    camera: CameraCreate
):

    obj = Camera(
        name=camera.name,
        status=camera.status,
        nvr=camera.nvr,
        ip=camera.ip
    )

    db.add(
        obj
    )

    db.commit()

    db.refresh(
        obj
    )

    return obj


# ==========================================================
# MODULE LOAD MESSAGE
# ==========================================================

print(
    "✅ VisionGuard AI CACHE CRUD loaded"
)

print(
    f"✅ Configured NVRs: "
    f"{len(NVRS)}"
)