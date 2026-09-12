from flask import Flask, request, jsonify, send_from_directory, send_file
import json, os, time, re, hashlib, hmac, urllib.parse

from config import IPS_FILE
from key_manager import (
    bind_key_by_device,
    load_license_keys,
    save_license_keys,
    normalize_key,
)

app = Flask(__name__)
MATERIAL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game_patches"))
MINIAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "miniapp")
MOD_SAFETY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mod_safety_status.json")

def load_mod_safety_status():
    """Load modification safety status"""
    if not os.path.exists(MOD_SAFETY_FILE):
        default = {
            "9999": {"name": "Drag Only", "status": "safe", "updated_at": 0, "updated_by": None},
            "9998": {"name": "Antenna Hand", "status": "safe", "updated_at": 0, "updated_by": None},
            "9997": {"name": "Magic Bullet", "status": "not_safe", "updated_at": 0, "updated_by": None},
            "9996": {"name": "Body 90%", "status": "safe", "updated_at": 0, "updated_by": None},
            "9995": {"name": "Drag + Antenna", "status": "safe", "updated_at": 0, "updated_by": None}
        }
        save_mod_safety_status(default)
        return default
    try:
        with open(MOD_SAFETY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_mod_safety_status(data):
    """Save modification safety status"""
    os.makedirs(os.path.dirname(MOD_SAFETY_FILE), exist_ok=True)
    with open(MOD_SAFETY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _verify_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """
    Validate Telegram WebApp initData signature server-side.
    """
    if not init_data or not bot_token:
        return False
    parsed = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
    data = dict(parsed)
    recv_hash = data.pop("hash", None)
    if not recv_hash:
        return False
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calc_hash, recv_hash)

def _parse_ipv4(s):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", (s or "").strip())
    if not m:
        return None
    parts = [int(x) for x in m.groups()]
    if any(p < 0 or p > 255 for p in parts):
        return None
    return ".".join(str(p) for p in parts)

def is_allowed(ip):
    if not os.path.exists(IPS_FILE): 
        return False
    try:
        with open(IPS_FILE, "r") as f:
            db = json.load(f)
        return ip in db and db[ip]['expires_at'] > time.time()
    except: 
        return False

def _is_system_frozen():
    try:
        freeze_file = os.path.join(os.path.dirname(IPS_FILE), "freeze_state.json")
        if not os.path.exists(freeze_file):
            return False
        with open(freeze_file, "r", encoding="utf-8") as f:
            st = json.load(f)
        return bool(st.get("frozen", False))
    except Exception:
        return False

@app.route('/check_auth')
def check_auth():
    ip = request.remote_addr
    if is_allowed(ip):
        return jsonify({"status": "success", "msg": "Nitro Proxy: License Active"}), 200
    return jsonify({"status": "fail", "msg": f"IP {ip} is not active!"}), 403

@app.route('/game_patches/<filename>')
def get_material(filename):
    if is_allowed(request.remote_addr):
        return send_from_directory(MATERIAL_DIR, filename)
    return "Unauthorized Access", 403

@app.route('/miniapp')
def miniapp_index():
    return send_from_directory(MINIAPP_DIR, "index.html")

@app.route('/miniapp/tutorial')
def miniapp_tutorial():
    return send_from_directory(MINIAPP_DIR, "tutorial.html")

@app.route('/miniapp/files/<path:filename>')
def miniapp_files(filename):
    files_dir = os.path.join(MINIAPP_DIR, "files")
    lower = str(filename).lower()
    is_video = lower.endswith(".mp4") or lower.endswith(".webm") or lower.endswith(".mov")
    # Keep certificate as download, but stream video files inline.
    if not is_video:
        full_path = os.path.join(files_dir, filename)
        if not os.path.isfile(full_path):
            return "File not found", 404
        download_filename = "NitroXMitm.crt" if lower.endswith(".pem") else os.path.basename(filename)
        resp = send_file(
            full_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype="application/octet-stream",
        )
        resp.headers["Content-Disposition"] = f'attachment; filename="{download_filename}"'
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    full_path = os.path.join(files_dir, filename)
    if not os.path.isfile(full_path):
        return "File not found", 404

    # Better compatibility with mobile webviews (iOS/Telegram): enable conditional/range responses.
    resp = send_file(full_path, as_attachment=False, conditional=True)
    resp.headers["Accept-Ranges"] = "bytes"
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp

@app.route('/miniapp/files')
def miniapp_files_index():
    """
    Auto-discover tutorial video in miniapp/files folder.
    Priority order is stable so replacing same filename is easy.
    """
    files_dir = os.path.join(MINIAPP_DIR, "files")
    if not os.path.isdir(files_dir):
        return jsonify({"ok": False, "url": None}), 200

    preferred = [
        "tutorial.mp4", "video.mp4",
        "tutorial.webm", "video.webm",
        "tutorial.mov", "video.mov",
    ]
    for name in preferred:
        p = os.path.join(files_dir, name)
        if os.path.isfile(p):
            return jsonify({"ok": True, "url": f"/miniapp/files/{name}"}), 200

    exts = (".mp4", ".webm", ".mov", ".m4v")
    for name in sorted(os.listdir(files_dir)):
        if name.lower().endswith(exts):
            p = os.path.join(files_dir, name)
            if os.path.isfile(p):
                return jsonify({"ok": True, "url": f"/miniapp/files/{name}"}), 200
    return jsonify({"ok": False, "url": None}), 200

@app.route('/miniapp/activate', methods=['POST'])
def miniapp_activate():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        tg_id = str(payload.get("telegram_id", "")).strip()
        init_data = str(payload.get("init_data", "")).strip()
        key_raw = str(payload.get("key", "")).strip()
        ip_raw = str(payload.get("ip", "")).strip()
        device_token = str(payload.get("device_token", "")).strip()
        client_ip = _parse_ipv4(ip_raw) or request.remote_addr

        if not key_raw or not client_ip:
            return jsonify({"ok": False, "error": "missing_fields"}), 400
        if not device_token:
            return jsonify({"ok": False, "error": "missing_device_token"}), 400
        # Reject forged clients: require Telegram WebApp signed initData.
        try:
            from config import TOKENS
            if not _verify_telegram_init_data(init_data, TOKENS.get("user", "")):
                return jsonify({"ok": False, "error": "invalid_telegram_init_data"}), 403
        except Exception:
            return jsonify({"ok": False, "error": "telegram_verification_failed"}), 403

        ok, err = bind_key_by_device(key_raw, client_ip, device_token, tg_id or None)
        if not ok:
            return jsonify({"ok": False, "error": err}), 403

        key = normalize_key(key_raw)
        keys = load_license_keys()
        rec = keys.get(key, {})
        if device_token:
            rec["device_token"] = device_token
            rec["device_bound_at"] = time.time()
            keys[key] = rec
            save_license_keys(keys)

        return jsonify({
            "ok": True,
            "key": key,
            "ip": rec.get("activated_ip", client_ip),
            "expires_at": rec.get("expires_at", 0),
        }), 200
    except Exception as e:
        traceback.print_exc()
        raise

@app.route('/miniapp/status', methods=['POST'])
def miniapp_status():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        ip = _parse_ipv4(str(payload.get("ip", "")).strip())
        device_token = str(payload.get("device_token", "")).strip()
        tg_id = str(payload.get("telegram_id", "")).strip()
        init_data = str(payload.get("init_data", "")).strip()

        if not device_token:
            return jsonify({"ok": False, "error": "missing_device_token"}), 400
        try:
            from config import TOKENS
            if not _verify_telegram_init_data(init_data, TOKENS.get("user", "")):
                return jsonify({"ok": False, "error": "invalid_telegram_init_data"}), 403
        except Exception:
            return jsonify({"ok": False, "error": "telegram_verification_failed"}), 403

        now = time.time()
        keys = load_license_keys()
        active = []
        updated = False
        for key, rec in keys.items():
            if rec.get("status") != "active":
                continue
            if float(rec.get("expires_at", 0) or 0) <= now:
                continue
            if str(rec.get("device_token", "")).strip() != device_token:
                continue
            if tg_id and str(rec.get("telegram_user", "")).strip() not in ("", tg_id):
                continue

            # Auto-rebind IP when network changes for the same device token.
            if ip and rec.get("activated_ip") != ip:
                ok, err = bind_key_by_device(key, ip, device_token, tg_id or None)
                if ok:
                    updated = True
                    rec = load_license_keys().get(key, rec)

            active.append({
                "key": key,
                "ip": rec.get("activated_ip"),
                "expires_at": rec.get("expires_at", 0),
                "duration_days": rec.get("duration_days", 0),
            })

        if updated:
            keys = load_license_keys()
        return jsonify({"ok": True, "active": active, "frozen": _is_system_frozen()}), 200
    except Exception as e:
        traceback.print_exc()
        raise

@app.route('/miniapp/mod_safety', methods=['GET'])
def get_mod_safety():
    """Get modification safety status for tutorial page"""
    try:
        status = load_mod_safety_status()
        return jsonify({"ok": True, "mods": status}), 200
    except Exception as e:
        traceback.print_exc()
        raise

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🔒 Nitro Proxy - Auth Server")
    print("="*50)
    print("✅ Server running on http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
