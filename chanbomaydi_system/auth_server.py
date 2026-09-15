from flask import Flask, request, jsonify, send_from_directory, send_file, abort
import json
import os
import time
import re
import hashlib
import hmac
import urllib.parse
import traceback

from config import IPS_FILE
from key_manager import (
    bind_key_by_device,
    load_license_keys,
    save_license_keys,
    normalize_key,
)

# ============================================================
# TIGRAN AI / FIREBASE
# ============================================================

from account_auth import account_bp
from ai_api import ai_bp


app = Flask(__name__)

app.register_blueprint(account_bp)
app.register_blueprint(ai_bp)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATERIAL_DIR = os.path.normpath(
    os.path.join(BASE_DIR, "..", "game_patches")
)

MINIAPP_DIR = os.path.join(
    BASE_DIR,
    "miniapp"
)

MINIAPP_FILES_DIR = os.path.join(
    MINIAPP_DIR,
    "files"
)

MOD_SAFETY_FILE = os.path.join(
    BASE_DIR,
    "data",
    "mod_safety_status.json"
)


# ============================================================
# SAFE DIRECT DOWNLOADS
# ============================================================

ALLOWED_DOWNLOADS = {
    "TigranXMitm.crt",
}


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):

    filename = os.path.basename(filename)

    if filename not in ALLOWED_DOWNLOADS:
        abort(404)

    full_path = os.path.join(
        MINIAPP_FILES_DIR,
        filename
    )

    if not os.path.isfile(full_path):
        return jsonify({
            "ok": False,
            "error": "file_not_found"
        }), 404

    response = send_from_directory(
        MINIAPP_FILES_DIR,
        filename,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream",
        conditional=True,
    )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-cache"

    return response


# ============================================================
# MOD STATUS
# ============================================================

def load_mod_safety_status():
    """Load modification safety status"""

    if not os.path.exists(MOD_SAFETY_FILE):

        default = {
            "9999": {
                "name": "Drag Only",
                "status": "safe",
                "updated_at": 0,
                "updated_by": None
            },

            "9998": {
                "name": "Antenna Hand",
                "status": "safe",
                "updated_at": 0,
                "updated_by": None
            },

            "9997": {
                "name": "Magic Bullet",
                "status": "not_safe",
                "updated_at": 0,
                "updated_by": None
            },

            "9996": {
                "name": "Body 90%",
                "status": "safe",
                "updated_at": 0,
                "updated_by": None
            },

            "9995": {
                "name": "Drag + Antenna",
                "status": "safe",
                "updated_at": 0,
                "updated_by": None
            }
        }

        save_mod_safety_status(default)

        return default

    try:

        with open(
            MOD_SAFETY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save_mod_safety_status(data):
    """Save modification safety status"""

    os.makedirs(
        os.path.dirname(MOD_SAFETY_FILE),
        exist_ok=True
    )

    with open(
        MOD_SAFETY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# TELEGRAM VALIDATION
# ============================================================

def _verify_telegram_init_data(
    init_data: str,
    bot_token: str
) -> bool:

    """
    Validate Telegram WebApp initData signature server-side.
    """

    if not init_data or not bot_token:
        return False

    parsed = urllib.parse.parse_qsl(
        init_data,
        keep_blank_values=True
    )

    data = dict(parsed)

    recv_hash = data.pop(
        "hash",
        None
    )

    if not recv_hash:
        return False

    data_check_string = "\n".join(
        f"{k}={v}"
        for k, v in sorted(data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256
    ).digest()

    calc_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        calc_hash,
        recv_hash
    )


# ============================================================
# IP
# ============================================================

def _parse_ipv4(s):

    m = re.match(
        r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$",
        (s or "").strip()
    )

    if not m:
        return None

    parts = [
        int(x)
        for x in m.groups()
    ]

    if any(
        p < 0 or p > 255
        for p in parts
    ):
        return None

    return ".".join(
        str(p)
        for p in parts
    )


def is_allowed(ip):

    if not os.path.exists(IPS_FILE):
        return False

    try:

        with open(
            IPS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            db = json.load(f)

        return (
            ip in db
            and db[ip]["expires_at"] > time.time()
        )

    except Exception:

        return False


# ============================================================
# FREEZE STATE
# ============================================================

def _is_system_frozen():

    try:

        freeze_file = os.path.join(
            os.path.dirname(IPS_FILE),
            "freeze_state.json"
        )

        if not os.path.exists(
            freeze_file
        ):
            return False

        with open(
            freeze_file,
            "r",
            encoding="utf-8"
        ) as f:

            st = json.load(f)

        return bool(
            st.get(
                "frozen",
                False
            )
        )

    except Exception:

        return False


# ============================================================
# AUTH
# ============================================================

@app.route("/check_auth")
def check_auth():

    ip = request.remote_addr

    if is_allowed(ip):

        return jsonify({
            "status": "success",
            "msg": "Tigran Proxy: License Active"
        }), 200

    return jsonify({
        "status": "fail",
        "msg": f"IP {ip} is not active!"
    }), 403


# Existing authenticated material route.
@app.route("/game_patches/<filename>")
def get_material(filename):

    if is_allowed(
        request.remote_addr
    ):

        return send_from_directory(
            MATERIAL_DIR,
            filename
        )

    return "Unauthorized Access", 403


# ============================================================
# MINI APP
# ============================================================

@app.route("/miniapp")
def miniapp_index():

    return send_from_directory(
        MINIAPP_DIR,
        "index.html"
    )

# ============================================================
# TIGRAN AI PAGES
# ============================================================

@app.route("/miniapp/login")
def miniapp_login():

    return send_from_directory(
        MINIAPP_DIR,
        "login.html"
    )


@app.route("/miniapp/ai")
def miniapp_ai():

    return send_from_directory(
        MINIAPP_DIR,
        "ai.html"
    )


@app.route("/miniapp/js/<path:filename>")
def miniapp_js(filename):

    return send_from_directory(
        os.path.join(
            MINIAPP_DIR,
            "js"
        ),
        filename
    )
    
@app.route("/miniapp/tutorial")
def miniapp_tutorial():

    return send_from_directory(
        MINIAPP_DIR,
        "tutorial.html"
    )


@app.route("/miniapp/files/<path:filename>")
def miniapp_files(filename):

    files_dir = MINIAPP_FILES_DIR

    lower = str(
        filename
    ).lower()

    is_video = (
        lower.endswith(".mp4")
        or lower.endswith(".webm")
        or lower.endswith(".mov")
        or lower.endswith(".m4v")
    )

    full_path = os.path.join(
        files_dir,
        filename
    )

    if not os.path.isfile(
        full_path
    ):

        return "File not found", 404

    # Video files can be streamed in the Mini App.
    if is_video:

        resp = send_file(
            full_path,
            as_attachment=False,
            conditional=True
        )

        resp.headers[
            "Accept-Ranges"
        ] = "bytes"

        resp.headers[
            "Cache-Control"
        ] = "public, max-age=300"

        return resp

    # Certificates are not distributed automatically.
    blocked_extensions = (
        ".crt",
        ".cer",
        ".pem",
    )

    if lower.endswith(
        blocked_extensions
    ):

        return jsonify({
            "ok": False,
            "error": "file_not_available"
        }), 403

    # Other ordinary files.
    download_filename = os.path.basename(
        filename
    )

    resp = send_file(
        full_path,
        as_attachment=True,
        download_name=download_filename,
        mimetype="application/octet-stream"
    )

    resp.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    return resp


@app.route("/miniapp/files")
def miniapp_files_index():

    """
    Auto-discover tutorial video
    in miniapp/files folder.
    """

    files_dir = MINIAPP_FILES_DIR

    if not os.path.isdir(
        files_dir
    ):

        return jsonify({
            "ok": False,
            "url": None
        }), 200

    preferred = [
        "tutorial.mp4",
        "video.mp4",
        "tutorial.webm",
        "video.webm",
        "tutorial.mov",
        "video.mov"
    ]

    for name in preferred:

        p = os.path.join(
            files_dir,
            name
        )

        if os.path.isfile(p):

            return jsonify({
                "ok": True,
                "url": f"/miniapp/files/{name}"
            }), 200

    exts = (
        ".mp4",
        ".webm",
        ".mov",
        ".m4v"
    )

    for name in sorted(
        os.listdir(files_dir)
    ):

        if name.lower().endswith(
            exts
        ):

            p = os.path.join(
                files_dir,
                name
            )

            if os.path.isfile(p):

                return jsonify({
                    "ok": True,
                    "url": f"/miniapp/files/{name}"
                }), 200

    return jsonify({
        "ok": False,
        "url": None
    }), 200


# ============================================================
# LICENSE ACTIVATION
# ============================================================

@app.route(
    "/miniapp/activate",
    methods=["POST"]
)
def miniapp_activate():

    try:

        payload = request.get_json(
            force=True,
            silent=True
        ) or {}

        tg_id = str(
            payload.get(
                "telegram_id",
                ""
            )
        ).strip()

        init_data = str(
            payload.get(
                "init_data",
                ""
            )
        ).strip()

        key_raw = str(
            payload.get(
                "key",
                ""
            )
        ).strip()

        ip_raw = str(
            payload.get(
                "ip",
                ""
            )
        ).strip()

        device_token = str(
            payload.get(
                "device_token",
                ""
            )
        ).strip()

        client_ip = (
            _parse_ipv4(ip_raw)
            or request.remote_addr
        )

        if (
            not key_raw
            or not client_ip
        ):

            return jsonify({
                "ok": False,
                "error": "missing_fields"
            }), 400

        if not device_token:

            return jsonify({
                "ok": False,
                "error": "missing_device_token"
            }), 400

        try:

            from config import TOKENS

            if not _verify_telegram_init_data(
                init_data,
                TOKENS.get(
                    "user",
                    ""
                )
            ):

                return jsonify({
                    "ok": False,
                    "error": "invalid_telegram_init_data"
                }), 403

        except Exception:

            return jsonify({
                "ok": False,
                "error": "telegram_verification_failed"
            }), 403

        ok, err = bind_key_by_device(
            key_raw,
            client_ip,
            device_token,
            tg_id or None
        )

        if not ok:

            return jsonify({
                "ok": False,
                "error": err
            }), 403

        key = normalize_key(
            key_raw
        )

        keys = load_license_keys()

        rec = keys.get(
            key,
            {}
        )

        if device_token:

            rec[
                "device_token"
            ] = device_token

            rec[
                "device_bound_at"
            ] = time.time()

            keys[
                key
            ] = rec

            save_license_keys(
                keys
            )

        return jsonify({
            "ok": True,
            "key": key,
            "ip": rec.get(
                "activated_ip",
                client_ip
            ),
            "expires_at": rec.get(
                "expires_at",
                0
            )
        }), 200

    except Exception:

        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": "internal_server_error"
        }), 500


# ============================================================
# LICENSE STATUS
# ============================================================

@app.route(
    "/miniapp/status",
    methods=["POST"]
)
def miniapp_status():

    try:

        payload = request.get_json(
            force=True,
            silent=True
        ) or {}

        ip = _parse_ipv4(
            str(
                payload.get(
                    "ip",
                    ""
                )
            ).strip()
        )

        device_token = str(
            payload.get(
                "device_token",
                ""
            )
        ).strip()

        tg_id = str(
            payload.get(
                "telegram_id",
                ""
            )
        ).strip()

        init_data = str(
            payload.get(
                "init_data",
                ""
            )
        ).strip()

        if not device_token:

            return jsonify({
                "ok": False,
                "error": "missing_device_token"
            }), 400

        try:

            from config import TOKENS

            if not _verify_telegram_init_data(
                init_data,
                TOKENS.get(
                    "user",
                    ""
                )
            ):

                return jsonify({
                    "ok": False,
                    "error": "invalid_telegram_init_data"
                }), 403

        except Exception:

            return jsonify({
                "ok": False,
                "error": "telegram_verification_failed"
            }), 403

        now = time.time()

        keys = load_license_keys()

        active = []

        updated = False

        for key, rec in keys.items():

            if rec.get(
                "status"
            ) != "active":
                continue

            if float(
                rec.get(
                    "expires_at",
                    0
                ) or 0
            ) <= now:
                continue

            if str(
                rec.get(
                    "device_token",
                    ""
                )
            ).strip() != device_token:
                continue

            if (
                tg_id
                and str(
                    rec.get(
                        "telegram_user",
                        ""
                    )
                ).strip()
                not in (
                    "",
                    tg_id
                )
            ):
                continue

            if (
                ip
                and rec.get(
                    "activated_ip"
                ) != ip
            ):

                ok, err = bind_key_by_device(
                    key,
                    ip,
                    device_token,
                    tg_id or None
                )

                if ok:

                    updated = True

                    rec = load_license_keys().get(
                        key,
                        rec
                    )

            active.append({
                "key": key,
                "ip": rec.get(
                    "activated_ip"
                ),
                "expires_at": rec.get(
                    "expires_at",
                    0
                ),
                "duration_days": rec.get(
                    "duration_days",
                    0
                )
            })

        if updated:

            keys = load_license_keys()

        return jsonify({
            "ok": True,
            "active": active,
            "frozen": _is_system_frozen()
        }), 200

    except Exception:

        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": "internal_server_error"
        }), 500


# ============================================================
# MOD STATUS API
# ============================================================

@app.route(
    "/miniapp/mod_safety",
    methods=["GET"]
)
def get_mod_safety():

    try:

        status = load_mod_safety_status()

        return jsonify({
            "ok": True,
            "mods": status
        }), 200

    except Exception:

        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": "internal_server_error"
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return {
        "ok": True,
        "status": "running"
    }, 200


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    print(
        f"✅ Server running on port {port}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
