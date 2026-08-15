# ==========================================================
# VisionGuard AI Enterprise Email Service
# ==========================================================

import os
import html
import smtplib

from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from .config import (
    EMAIL_BRAND,
    SMTP_USERNAME as CONFIG_SMTP_USERNAME,
    SMTP_PASSWORD as CONFIG_SMTP_PASSWORD,
    RECEIVER_EMAIL as CONFIG_RECEIVER_EMAIL,
)


# ==========================================================
# SMTP CONFIGURATION
# ==========================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# ==========================================================
# ENVIRONMENT VARIABLES
#
# Windows:
#
# setx VISIONGUARD_SENDER_EMAIL "your@email.com"
# setx VISIONGUARD_APP_PASSWORD "YOUR_APP_PASSWORD"
# setx VISIONGUARD_RECEIVER_EMAIL "receiver@email.com"
#
# IMPORTANT:
# Restart CMD after setx.
# ==========================================================

SENDER_EMAIL = os.getenv(
    "VISIONGUARD_SENDER_EMAIL",
    CONFIG_SMTP_USERNAME
).strip()

APP_PASSWORD = os.getenv(
    "VISIONGUARD_APP_PASSWORD",
    CONFIG_SMTP_PASSWORD
).strip()

RECEIVER_EMAIL = os.getenv(
    "VISIONGUARD_RECEIVER_EMAIL",
    CONFIG_RECEIVER_EMAIL
).strip()


# ==========================================================
# TEMPLATE DIRECTORY
# ==========================================================

TEMPLATE_DIR = (
    Path(__file__).parent /
    "templates"
)


# ==========================================================
# TEMPLATE RENDERER
# ==========================================================

def render_template(
    template_name: str,
    data: dict
):

    template_path = (
        TEMPLATE_DIR /
        template_name
    )

    if not template_path.exists():

        raise FileNotFoundError(
            f"Email template not found: "
            f"{template_path}"
        )

    with open(
        template_path,
        "r",
        encoding="utf-8"
    ) as f:

        html_content = f.read()

    for key, value in data.items():

        html_content = html_content.replace(
            "{{" + key + "}}",
            str(value)
        )

    return html_content


# ==========================================================
# EMAIL LOGGER
# ==========================================================

def log_email_success(subject):

    print()
    print("=" * 70)
    print("✅ EMAIL SENT")
    print("=" * 70)
    print("Subject :", subject)
    print("=" * 70)
    print()


def log_email_failure(
    subject,
    error
):

    print()
    print("=" * 70)
    print("❌ EMAIL FAILED")
    print("=" * 70)
    print("Subject :", subject)
    print("Error   :", error)
    print("=" * 70)
    print()


# ==========================================================
# SMTP VALIDATION
# ==========================================================

def validate_smtp_config():

    valid = True

    if not SENDER_EMAIL:

        print(
            "❌ VISIONGUARD_SENDER_EMAIL "
            "is not configured"
        )

        valid = False

    if not APP_PASSWORD:

        print(
            "❌ VISIONGUARD_APP_PASSWORD "
            "is not configured"
        )

        valid = False

    if not RECEIVER_EMAIL:

        print(
            "❌ VISIONGUARD_RECEIVER_EMAIL "
            "is not configured"
        )

        valid = False

    return valid


# ==========================================================
# GENERIC HTML EMAIL SENDER
# ==========================================================

def send_html_email(
    *,
    subject: str,
    template_name: str,
    camera: str,
    nvr: str,
    ip: str,
    status: str,
    event_time: str,
    attachment_path: str = "",
):

    try:

        if not validate_smtp_config():

            return False

        html_content = render_template(

            template_name,

            {

                "brand":
                    html.escape(
                        str(EMAIL_BRAND)
                    ),

                "camera":
                    html.escape(
                        str(camera)
                    ),

                "nvr":
                    html.escape(
                        str(nvr)
                    ),

                "ip":
                    html.escape(
                        str(ip)
                    ),

                "status":
                    html.escape(
                        str(status)
                    ),

                "issues":
                    html.escape(
                        str(status)
                    ),

                "message":
                    html.escape(
                        str(status)
                    ),

                "time":
                    html.escape(
                        str(event_time)
                    ),

                "event_time":
                    html.escape(
                        str(event_time)
                    )

            }

        )

        msg = MIMEMultipart(
            "alternative"
        )

        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        msg.attach(

            MIMEText(
                html_content,
                "html",
                "utf-8"
            )

        )

        # --------------------------------------------------
        # OPTIONAL CAMERA ANGLE EVIDENCE ATTACHMENT
        # --------------------------------------------------
        if attachment_path:
            evidence = Path(str(attachment_path))
            if evidence.exists() and evidence.is_file():
                with open(evidence, "rb") as image_file:
                    part = MIMEBase("image", "jpeg")
                    part.set_payload(image_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{evidence.name}"',
                )
                msg.attach(part)
                print("📷 Angle evidence attached:", evidence)

        # --------------------------------------------------
        # DEBUG
        # --------------------------------------------------

        print()
        print(
            "========== EMAIL DEBUG =========="
        )

        print(
            "Subject :",
            subject
        )

        print(
            "Template:",
            template_name
        )

        print(
            "From    :",
            SENDER_EMAIL
        )

        print(
            "To      :",
            RECEIVER_EMAIL
        )

        print(
            "SMTP    :",
            f"{SMTP_SERVER}:{SMTP_PORT}"
        )

        print(
            "================================="
        )

        # --------------------------------------------------
        # SMTP CONNECTION
        # --------------------------------------------------

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=20
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            print(
                "✅ TLS OK"
            )

            server.login(
                SENDER_EMAIL,
                APP_PASSWORD
            )

            print(
                "✅ LOGIN SUCCESS"
            )

            server.sendmail(

                SENDER_EMAIL,

                RECEIVER_EMAIL,

                msg.as_string()

            )

            print(
                "✅ MAIL SENT SUCCESSFULLY"
            )

        log_email_success(
            subject
        )

        return True

    except Exception as e:

        log_email_failure(
            subject,
            e
        )

        return False


# ==========================================================
# GENERIC WARNING EMAIL
# ==========================================================

def send_warning_email(
    *,
    subject,
    template_name,
    camera,
    nvr,
    ip,
    message,
    event_time,
    attachment_path="",
):

    return send_html_email(

        subject=subject,

        template_name=template_name,

        camera=camera,

        nvr=nvr,

        ip=ip,

        status=message,

        event_time=event_time,

        attachment_path=attachment_path,

    )


# ==========================================================
# CAMERA OFFLINE
# ==========================================================

def send_offline_email(
    camera,
    nvr,
    ip,
    event_time
):

    return send_warning_email(

        subject=(
            f"🔴 [{nvr}] "
            f"Camera Offline - {camera}"
        ),

        template_name="offline.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message="Camera is Offline",

        event_time=event_time

    )


# ==========================================================
# CAMERA RECOVERY
# ==========================================================

def send_recovery_email(
    camera,
    nvr,
    ip,
    event_time
):

    return send_warning_email(

        subject=(
            f"🟢 [{nvr}] "
            f"Camera Recovered - {camera}"
        ),

        template_name="recovery.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message="Camera Restored Successfully",

        event_time=event_time

    )


# ==========================================================
# NVR OFFLINE EMAIL
# ==========================================================

def send_nvr_offline_email(
    *,
    nvr,
    cameras,
    event_time
):

    try:

        if not validate_smtp_config():

            return False

        cameras = cameras or []

        safe_nvr = html.escape(
            str(nvr)
        )

        safe_time = html.escape(
            str(event_time)
        )

        rows = ""

        for index, camera in enumerate(
            cameras,
            start=1
        ):

            name = html.escape(
                str(
                    camera.get(
                        "name",
                        "-"
                    )
                )
            )

            ip = html.escape(
                str(
                    camera.get(
                        "ip",
                        "-"
                    )
                )
            )

            camera_id = html.escape(
                str(
                    camera.get(
                        "id",
                        "-"
                    )
                )
            )

            rows += f"""
            <tr>
                <td>{index}</td>
                <td>{name}</td>
                <td>{camera_id}</td>
                <td>{ip}</td>
                <td class="offline">
                    OFFLINE
                </td>
            </tr>
            """

        if not rows:

            rows = """
            <tr>
                <td colspan="5">
                    No camera inventory available
                </td>
            </tr>
            """

        subject = (
            f"🚨 [{nvr}] NVR OFFLINE "
            f"- {len(cameras)} Cameras Affected"
        )

        body = f"""
        <!DOCTYPE html>

        <html>

        <head>

            <meta charset="UTF-8">

            <style>

                body {{
                    font-family:
                        Arial,
                        Helvetica,
                        sans-serif;

                    background:
                        #f4f6f8;

                    padding:
                        20px;
                }}

                .container {{
                    max-width:
                        900px;

                    margin:
                        auto;

                    background:
                        white;

                    border-radius:
                        10px;

                    overflow:
                        hidden;

                    box-shadow:
                        0 2px 10px
                        rgba(0,0,0,0.08);
                }}

                .header {{
                    padding:
                        24px;

                    background:
                        #b91c1c;

                    color:
                        white;
                }}

                .content {{
                    padding:
                        24px;
                }}

                .box {{
                    padding:
                        15px;

                    background:
                        #f8fafc;

                    border:
                        1px solid
                        #e2e8f0;

                    border-radius:
                        8px;

                    margin-bottom:
                        10px;
                }}

                table {{
                    width:
                        100%;

                    border-collapse:
                        collapse;
                }}

                th {{
                    background:
                        #f1f5f9;

                    text-align:
                        left;
                }}

                th,
                td {{
                    padding:
                        10px;

                    border-bottom:
                        1px solid
                        #e5e7eb;

                    font-size:
                        13px;
                }}

                .offline {{
                    color:
                        #b91c1c;

                    font-weight:
                        bold;
                }}

                .footer {{
                    padding:
                        18px 24px;

                    background:
                        #f8fafc;

                    color:
                        #64748b;

                    font-size:
                        12px;
                }}

            </style>

        </head>

        <body>

            <div class="container">

                <div class="header">

                    <h1>
                        🚨 NVR OFFLINE
                    </h1>

                    <p>
                        {html.escape(str(EMAIL_BRAND))}
                    </p>

                </div>

                <div class="content">

                    <div class="box">

                        <strong>
                            NVR:
                        </strong>

                        {safe_nvr}

                    </div>

                    <div class="box">

                        <strong>
                            Status:
                        </strong>

                        <span class="offline">
                            OFFLINE
                        </span>

                    </div>

                    <div class="box">

                        <strong>
                            Affected Cameras:
                        </strong>

                        {len(cameras)}

                    </div>

                    <div class="box">

                        <strong>
                            Detected At:
                        </strong>

                        {safe_time}

                    </div>

                    <h2>
                        Affected Cameras
                    </h2>

                    <table>

                        <thead>

                            <tr>

                                <th>#</th>

                                <th>
                                    Camera
                                </th>

                                <th>
                                    ID
                                </th>

                                <th>
                                    IP
                                </th>

                                <th>
                                    Status
                                </th>

                            </tr>

                        </thead>

                        <tbody>

                            {rows}

                        </tbody>

                    </table>

                </div>

                <div class="footer">

                    VisionGuard AI -
                    Automated NVR Monitoring Alert

                </div>

            </div>

        </body>

        </html>
        """

        msg = MIMEMultipart(
            "alternative"
        )

        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "html",
                "utf-8"
            )
        )

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=20
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            print("✅ NVR OFFLINE TLS OK")

            server.login(
                SENDER_EMAIL,
                APP_PASSWORD
            )

            print(
                "✅ NVR OFFLINE LOGIN SUCCESS"
            )

            server.sendmail(
                SENDER_EMAIL,
                RECEIVER_EMAIL,
                msg.as_string()
            )

            print(
                "✅ NVR OFFLINE MAIL SENT"
            )

        log_email_success(
            subject
        )

        return True

    except Exception as e:

        log_email_failure(
            "NVR OFFLINE EMAIL",
            e
        )

        return False


# ==========================================================
# NVR RECOVERY EMAIL
# ==========================================================

def send_nvr_recovery_email(
    *,
    nvr,
    cameras,
    event_time
):

    try:

        if not validate_smtp_config():

            return False

        cameras = cameras or []

        safe_nvr = html.escape(
            str(nvr)
        )

        safe_time = html.escape(
            str(event_time)
        )

        rows = ""

        for index, camera in enumerate(
            cameras,
            start=1
        ):

            name = html.escape(
                str(
                    camera.get(
                        "name",
                        "-"
                    )
                )
            )

            ip = html.escape(
                str(
                    camera.get(
                        "ip",
                        "-"
                    )
                )
            )

            rows += f"""
            <tr>
                <td>{index}</td>
                <td>{name}</td>
                <td>{ip}</td>
                <td class="online">
                    ONLINE
                </td>
            </tr>
            """

        if not rows:

            rows = """
            <tr>
                <td colspan="4">
                    No camera inventory available
                </td>
            </tr>
            """

        subject = (
            f"✅ [{nvr}] NVR RECOVERED "
            f"- {len(cameras)} Cameras Restored"
        )

        body = f"""
        <!DOCTYPE html>

        <html>

        <head>

            <meta charset="UTF-8">

            <style>

                body {{
                    font-family:
                        Arial,
                        Helvetica,
                        sans-serif;

                    background:
                        #f4f6f8;

                    padding:
                        20px;
                }}

                .container {{
                    max-width:
                        900px;

                    margin:
                        auto;

                    background:
                        white;

                    border-radius:
                        10px;

                    overflow:
                        hidden;

                    box-shadow:
                        0 2px 10px
                        rgba(0,0,0,0.08);
                }}

                .header {{
                    padding:
                        24px;

                    background:
                        #15803d;

                    color:
                        white;
                }}

                .content {{
                    padding:
                        24px;
                }}

                .box {{
                    padding:
                        15px;

                    background:
                        #f8fafc;

                    border:
                        1px solid
                        #e2e8f0;

                    border-radius:
                        8px;

                    margin-bottom:
                        10px;
                }}

                table {{
                    width:
                        100%;

                    border-collapse:
                        collapse;
                }}

                th {{
                    background:
                        #f1f5f9;

                    text-align:
                        left;
                }}

                th,
                td {{
                    padding:
                        10px;

                    border-bottom:
                        1px solid
                        #e5e7eb;

                    font-size:
                        13px;
                }}

                .online {{
                    color:
                        #15803d;

                    font-weight:
                        bold;
                }}

                .footer {{
                    padding:
                        18px 24px;

                    background:
                        #f8fafc;

                    color:
                        #64748b;

                    font-size:
                        12px;
                }}

            </style>

        </head>

        <body>

            <div class="container">

                <div class="header">

                    <h1>
                        ✅ NVR RECOVERED
                    </h1>

                    <p>
                        {html.escape(str(EMAIL_BRAND))}
                    </p>

                </div>

                <div class="content">

                    <div class="box">

                        <strong>
                            NVR:
                        </strong>

                        {safe_nvr}

                    </div>

                    <div class="box">

                        <strong>
                            Status:
                        </strong>

                        <span class="online">
                            ONLINE
                        </span>

                    </div>

                    <div class="box">

                        <strong>
                            Cameras Restored:
                        </strong>

                        {len(cameras)}

                    </div>

                    <div class="box">

                        <strong>
                            Recovery Time:
                        </strong>

                        {safe_time}

                    </div>

                    <h2>
                        Restored Cameras
                    </h2>

                    <table>

                        <thead>

                            <tr>

                                <th>#</th>

                                <th>
                                    Camera
                                </th>

                                <th>
                                    IP
                                </th>

                                <th>
                                    Status
                                </th>

                            </tr>

                        </thead>

                        <tbody>

                            {rows}

                        </tbody>

                    </table>

                </div>

                <div class="footer">

                    VisionGuard AI -
                    Automated NVR Monitoring Recovery

                </div>

            </div>

        </body>

        </html>
        """

        msg = MIMEMultipart(
            "alternative"
        )

        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "html",
                "utf-8"
            )
        )

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=20
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                SENDER_EMAIL,
                APP_PASSWORD
            )

            server.sendmail(
                SENDER_EMAIL,
                RECEIVER_EMAIL,
                msg.as_string()
            )

        log_email_success(
            subject
        )

        return True

    except Exception as e:

        log_email_failure(
            "NVR RECOVERY EMAIL",
            e
        )

        return False


# ==========================================================
# DEVICE IDENTITY EMAIL
# ==========================================================

def send_identity_email(
    camera,
    nvr,
    ip,
    issues,
    event_time
):

    return send_warning_email(

        subject=(
            f"🚨 [{nvr}] "
            f"Device Identity Changed - {camera}"
        ),

        template_name="identity.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message=issues,

        event_time=event_time

    )


# ==========================================================
# IP CONFLICT EMAIL
# ==========================================================

def send_ip_conflict_email(
    camera,
    nvr,
    ip,
    event_time
):

    return send_warning_email(

        subject=(
            f"⚠️ [{nvr}] "
            f"Duplicate IP Detected"
        ),

        template_name="ip_conflict.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message="Duplicate IP Detected",

        event_time=event_time

    )


# ==========================================================
# IP CONFLICT RESOLVED
# ==========================================================

def send_ip_conflict_resolved_email(
    event_time
):

    return send_warning_email(

        subject=(
            "✅ IP Conflict Resolved"
        ),

        template_name=(
            "ip_conflict_resolved.html"
        ),

        camera=(
            "All Monitored Cameras"
        ),

        nvr=(
            "All Connected NVRs"
        ),

        ip="-",

        message=(
            "No Duplicate IP Detected"
        ),

        event_time=event_time

    )


# ==========================================================
# VIDEO LOSS
# ==========================================================

def send_video_loss_email(
    camera,
    nvr,
    ip,
    event_time
):

    return send_warning_email(

        subject=(
            f"🎥 [{nvr}] "
            f"Video Loss - {camera}"
        ),

        template_name="video_loss.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message="Video Stream Lost",

        event_time=event_time

    )


# ==========================================================
# VIDEO RESTORED
# ==========================================================

def send_video_restored_email(
    camera,
    nvr,
    ip,
    event_time
):

    return send_warning_email(

        subject=(
            f"🟢 [{nvr}] "
            f"Video Restored - {camera}"
        ),

        template_name="video_restored.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message="Video Stream Restored",

        event_time=event_time

    )


# ==========================================================
# RECORDING LOSS
# ==========================================================

def send_recording_loss_email(
    camera,
    nvr,
    ip,
    loss_from,
    loss_to,
    duration
):

    print(
        "######## "
        "send_recording_loss_email "
        "CALLED ########"
    )

    return send_warning_email(

        subject=(
            f"⛔ [{nvr}] "
            f"Recording Loss - {camera}"
        ),

        template_name="video_loss.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message=(

            f"Recording Interrupted\n\n"

            f"Missing From : {loss_from}\n"

            f"Missing To   : {loss_to}\n"

            f"Duration     : {duration}"

        ),

        event_time=loss_from

    )


# ==========================================================
# RECORDING RECOVERY
# ==========================================================

def send_recording_recovery_email(
    camera,
    nvr,
    ip,
    loss_from,
    loss_to,
    restored_at,
    duration
):

    return send_warning_email(

        subject=(
            f"✅ [{nvr}] "
            f"Recording Restored - {camera}"
        ),

        template_name="video_restored.html",

        camera=camera,

        nvr=nvr,

        ip=ip,

        message=(

            f"Recording Restored\n\n"

            f"Loss From : {loss_from}\n"

            f"Loss To   : {loss_to}\n"

            f"Recovered : {restored_at}\n"

            f"Duration  : {duration}"

        ),

        event_time=restored_at

    )


# ==========================================================
# PTZ POSITION CHANGE
# ==========================================================

def send_ptz_position_changed_email(
    camera,
    nvr,
    ip,
    channel,
    change,
    event_time,
):

    return send_warning_email(

        subject=(
            f"🚨 [{nvr}] "
            f"PTZ Camera Position Changed - {camera}"
        ),

        template_name=(
            "ptz_position_changed.html"
        ),

        camera=camera,

        nvr=nvr,

        ip=ip,

        message=(
            f"Channel {channel}: {change}"
        ),

        event_time=event_time,

    )


# ==========================================================
# CAMERA ANGLE / VIEWPOINT CHANGE
# ==========================================================

def send_camera_angle_changed_email(
    camera,
    nvr,
    ip,
    channel,
    score,
    details,
    event_time,
):

    print()
    print("=" * 70)
    print("🚨 CAMERA ANGLE CHANGE EMAIL TRIGGERED")
    print("=" * 70)

    print("Camera  :", camera)
    print("NVR     :", nvr)
    print("IP      :", ip)
    print("Channel :", channel)
    print("Score   :", score)
    print("Details :", details)
    print("Time    :", event_time)

    print("=" * 70)

    evidence_path = ""
    marker = "EVIDENCE_FILE="
    if marker in str(details):
        evidence_path = str(details).split(marker, 1)[1].split(" | ", 1)[0].strip()

    return send_warning_email(

        subject=(
            f"🚨 [{nvr}] "
            f"Camera Angle Changed - {camera}"
        ),

        template_name=(
            "camera_angle_changed.html"
        ),

        camera=camera,

        nvr=nvr,

        ip=ip,

        message=(
            f"Channel {channel}: "
            f"Visual viewpoint changed | "
            f"Score {score} | "
            f"{details}"
        ),

        event_time=event_time,

        attachment_path=evidence_path,

    )


# ==========================================================
# CAMERA ANGLE RESTORED
# ==========================================================

def send_camera_angle_restored_email(
    camera,
    nvr,
    ip,
    channel,
    event_time,
):

    print()
    print("=" * 70)
    print("🟢 CAMERA ANGLE RESTORED EMAIL TRIGGERED")
    print("=" * 70)

    print("Camera  :", camera)
    print("NVR     :", nvr)
    print("IP      :", ip)
    print("Channel :", channel)
    print("Time    :", event_time)

    print("=" * 70)

    return send_warning_email(

        subject=(
            f"🟢 [{nvr}] "
            f"Camera Angle Restored - {camera}"
        ),

        template_name=(
            "camera_angle_restored.html"
        ),

        camera=camera,

        nvr=nvr,

        ip=ip,

        message=(
            f"Channel {channel}: "
            f"Camera viewpoint returned "
            f"to the stored baseline."
        ),

        event_time=event_time,

    )


# ==========================================================
# MODULE LOAD
# ==========================================================

print(
    "✅ VisionGuard AI Enterprise Email Service Loaded"
)

print(
    "📧 SMTP Server :",
    f"{SMTP_SERVER}:{SMTP_PORT}"
)

print(
    "📧 Sender      :",
    SENDER_EMAIL if SENDER_EMAIL else "NOT CONFIGURED"
)

print(
    "📧 Receiver    :",
    RECEIVER_EMAIL if RECEIVER_EMAIL else "NOT CONFIGURED"
)

print(
    "📧 App Password:",
    "CONFIGURED" if APP_PASSWORD else "NOT CONFIGURED"
)

# ==========================================================
# CAMERA NVR MIGRATION
# ==========================================================

def send_camera_migration_email(
    camera, ip, old_nvr, old_channel, new_nvr, new_channel, event_time
):
    return send_warning_email(
        subject=f"🚨 Camera NVR Movement - {camera}",
        template_name="camera_migration.html",
        camera=camera,
        nvr=f"{old_nvr} → {new_nvr}",
        ip=ip,
        message=(
            f"Previous: {old_nvr} CH-{old_channel}\n"
            f"Current: {new_nvr} CH-{new_channel}"
        ),
        event_time=event_time,
    )
