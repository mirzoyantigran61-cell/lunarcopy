from __future__ import annotations

import os
import time
import secrets
import logging
from urllib.parse import urljoin

import requests
from flask import Flask, Response, jsonify, redirect, render_template_string, request
from flask_socketio import SocketIO, emit, join_room
from werkzeug.middleware.proxy_fix import ProxyFix

PORT = int(os.environ.get("PORT", "8080"))
UPSTREAM_BASE_URL = os.environ.get("UPSTREAM_BASE_URL", "http://127.0.0.1:9000").rstrip("/") + "/"
SESSION_TTL = int(os.environ.get("SESSION_TTL", str(12 * 60 * 60)))

# ============================================================
#  FIREBASE URL (твой)
# ============================================================
FIREBASE_URL = "https://yourtigranmods-papaji-devffsrc-default-rtdb.firebaseio.com"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

socketio = SocketIO(app, cors_allowed_origins=[], async_mode="threading")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("proxy-panel")

http = requests.Session()

DEFAULT_SWITCHES = {
    "Aim Profile": False,
    "Backjump Preset": False,
    "High Sensi": False,
    "Speed Preset": False,
    "Visual FX": False,
    "Motion Preset": False,
}

sessions: dict[str, dict] = {}

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}

def now() -> int:
    return int(time.time())

def cleanup_sessions() -> None:
    cutoff = now() - SESSION_TTL
    stale = [sid for sid, item in sessions.items() if item["created_at"] < cutoff]
    for sid in stale:
        sessions.pop(sid, None)

def get_session_id() -> str:
    return (request.headers.get("X-Session-ID") or request.args.get("session_id") or "").strip()

def get_session():
    cleanup_sessions()
    sid = get_session_id()
    if not sid:
        return None, None
    item = sessions.get(sid)
    if not item:
        return sid, None
    return sid, item

def require_session():
    sid, item = get_session()
    if item is None:
        return sid, None, (jsonify({"status": "error", "message": "invalid session"}), 401)
    return sid, item, None

def client_ip() -> str:
    return request.remote_addr or "unknown"

# ============================================================
#  ПРОВЕРКА АДМИНА / КЛЮЧА (твоя структура)
# ============================================================
def check_admin(username: str, password: str):
    try:
        r = requests.get(f"{FIREBASE_URL}/admins.json", timeout=5)
        if r.status_code == 200:
            admins = r.json() or {}
            for admin_data in admins.values():
                if admin_data.get("username") == username and admin_data.get("password") == password:
                    return admin_data.get("role", "admin")
        return None
    except:
        return None

def check_user(username: str, password: str):
    try:
        r = requests.get(f"{FIREBASE_URL}/keys/{username}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and data.get("password") == password:
                return True
        return False
    except:
        return False

def check_legacy_user(username: str, password: str):
    try:
        r_users = requests.get(f"{FIREBASE_URL}/users.json", timeout=5)
        r_roles = requests.get(f"{FIREBASE_URL}/roles.json", timeout=5)
        if r_users.status_code == 200 and r_roles.status_code == 200:
            users = r_users.json() or {}
            roles = r_roles.json() or {}
            if username in users.values():
                if password == roles.get("userPassword") or password == roles.get("adminPassword"):
                    return True
        return False
    except:
        return False

# ============================================================
#  HTML-ИНТЕРФЕЙС (HI CLIENT – из LUNAR, но с твоим названием)
# ============================================================
HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#070312">
<title>HI CLIENT</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:
 radial-gradient(900px 480px at 80% -10%,rgba(88,28,204,.55),transparent 60%),
 radial-gradient(700px 420px at 8% 105%,rgba(76,29,174,.45),transparent 60%),
 radial-gradient(600px 600px at 50% 50%,rgba(109,40,217,.18),transparent 70%),
 radial-gradient(400px 300px at 15% 20%,rgba(76,29,174,.20),transparent 60%),#070312;
 background-attachment:fixed;
 color:#d8d0f0;display:flex;justify-content:center;padding:22px;
 min-height:100dvh;overflow-x:hidden;overflow-y:auto}
body::before{content:"";position:fixed;inset:0;pointer-events:none;
 background:repeating-linear-gradient(0deg,rgba(109,40,217,.035) 0 1px,transparent 1px 3px)}
body::after{content:"";position:fixed;left:0;right:0;top:0;height:3px;pointer-events:none;
 background:linear-gradient(90deg,transparent,#7c3aed,#4f46e5,transparent);filter:blur(1px)}
.card{width:100%;max-width:400px;position:relative;margin:auto;background:linear-gradient(160deg,rgba(30,16,60,.94),rgba(12,6,30,.97));
 border:1px solid rgba(124,58,237,.45);border-radius:22px;padding:30px 24px;z-index:1;
 box-shadow:0 0 46px rgba(109,40,217,.38),0 0 90px rgba(79,70,229,.12),inset 0 0 30px rgba(124,58,237,.08);
 backdrop-filter:blur(12px)}
.card::before{content:"";position:absolute;inset:-1px;border-radius:22px;padding:1px;pointer-events:none;
 background:linear-gradient(135deg,rgba(124,58,237,.95),rgba(109,40,217,.2),rgba(79,70,229,.95));
 -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;
 mask-composite:exclude}
.brand{text-align:center;margin-bottom:22px}
.brand h1{font-size:25px;letter-spacing:2px;font-weight:800;
 background:linear-gradient(90deg,#a78bfa,#8b5cf6 45%,#6366f1 90%);-webkit-background-clip:text;background-clip:text;
 color:transparent;filter:drop-shadow(0 0 16px rgba(124,58,237,.6))}
.brand .sub{margin-top:8px;font-size:10px;letter-spacing:7px;color:rgba(167,139,250,.75);text-transform:uppercase}
input[type=text],input[type=password],input[type=number]{width:100%;height:52px;margin:9px 0;padding:0 16px;
 background:rgba(124,58,237,.10);border:1px solid rgba(139,92,246,.40);border-radius:13px;color:#fff;
 font-size:15px;text-align:center;letter-spacing:2px;outline:none;display:block;
 transition:border-color .2s,box-shadow .2s}
textarea{width:100%;margin:9px 0;padding:10px 14px;background:rgba(124,58,237,.10);
 border:1px solid rgba(139,92,246,.40);border-radius:13px;color:#fff;font-size:13px;outline:none;
 display:block;resize:vertical;min-height:60px;font-family:monospace;letter-spacing:.5px}
input:focus{border-color:#8b5cf6;box-shadow:0 0 20px rgba(124,58,237,.4),inset 0 0 12px rgba(139,92,246,.12)}
input::placeholder{color:rgba(200,190,240,.4);letter-spacing:1px}
button{width:100%;height:54px;margin-top:14px;border:none;border-radius:13px;font-size:15px;font-weight:800;
 letter-spacing:3px;cursor:pointer;color:#fff;display:block;
 background:linear-gradient(90deg,#6d28d9,#7c3aed 55%,#4f46e5);box-shadow:0 0 26px rgba(109,40,217,.5);
 transition:transform .12s,box-shadow .2s}
button:active{transform:scale(.97)}
.ghost{background:rgba(124,58,237,.12);box-shadow:none;border:1px solid rgba(124,58,237,.5)}
.msg{text-align:center;margin-top:14px;font-size:13px;min-height:18px;color:#a78bfa;letter-spacing:.5px}
.msg.ok{color:#2dffd0}
.hint{text-align:center;margin:14px 0 4px;font-size:11px;color:rgba(200,190,240,.5);letter-spacing:1px;line-height:1.7}
.stat{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;margin-top:10px;
 background:rgba(124,58,237,.10);border:1px solid rgba(139,92,246,.32);border-radius:13px;font-size:13px;gap:12px}
.stat span{color:rgba(200,190,240,.6);letter-spacing:1px;white-space:nowrap}
.stat b{color:#a78bfa;letter-spacing:1px;word-break:break-all;text-align:right}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
.actions button{height:44px;margin-top:0;font-size:12px;letter-spacing:2px;white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:11px}
.tblwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin-top:16px;
 border:1px solid rgba(124,58,237,.3);border-radius:13px;
 background:rgba(124,58,237,.06)}
.tblwrap table{width:100%;min-width:520px}
th,td{padding:9px 5px;text-align:center;border-bottom:1px solid rgba(124,58,237,.18);white-space:nowrap}
th{color:#a78bfa;letter-spacing:1px;font-size:9px;text-transform:uppercase;position:sticky;top:0;
 background:linear-gradient(160deg,rgba(30,16,60,.98),rgba(12,6,30,.98));z-index:1}
td .k{color:#c4b5fd;letter-spacing:.5px;font-family:monospace;font-size:10px;word-break:break-all;white-space:normal}
td .wr{color:#c4b5fd;font-family:monospace;font-size:10px;word-break:break-all;white-space:normal;max-width:180px;text-align:left}
.chip{display:inline-block;padding:3px 8px;border-radius:20px;font-size:10px;letter-spacing:1px}
.chip.on{color:#2dffd0;border:1px solid rgba(45,255,208,.4);background:rgba(45,255,208,.08)}
.chip.off{color:#ff8080;border:1px solid rgba(255,128,128,.4);background:rgba(255,128,128,.08)}
.del{background:#8b5cf6;height:30px;margin:0;width:62px;font-size:10px;padding:0;border-radius:8px;letter-spacing:1px}
.inrow{display:inline-flex;gap:6px;align-items:center}
.inrow .del{width:44px}
.inrow .cp{width:30px;height:30px;margin:0;padding:0;font-size:12px;border-radius:8px;
 background:rgba(124,58,237,.18);box-shadow:none;border:1px solid rgba(139,92,246,.45)}
.tcap{padding:9px 12px;font-size:10px;letter-spacing:3px;color:#a78bfa;
 border-bottom:1px solid rgba(124,58,237,.25)}
.row2 {display:flex;gap:8px;flex-wrap:wrap}
.row2 input{flex:1;min-width:96px}
.step{display:none;text-align:center;padding:8px 0}
.step.on{display:block}
.stepno{font-size:10px;letter-spacing:5px;color:#a78bfa;margin-bottom:16px}
.steptitle{font-size:19px;font-weight:800;letter-spacing:1px;line-height:1.4;margin-bottom:24px;color:#e9e2ff}
.join{display:flex;align-items:center;justify-content:center;gap:8px;height:52px;border-radius:13px;
 text-decoration:none;color:#fff;font-weight:800;letter-spacing:2px;font-size:14px;
 background:linear-gradient(90deg,#4f46e5,#8b5cf6);box-shadow:0 0 20px rgba(109,40,217,.45);
 transition:transform .12s,box-shadow .2s}
.join:active{transform:scale(.97)}
.join i{font-size:18px}
.backlink{display:block;text-align:center;margin-top:14px;font-size:11px;letter-spacing:1px;
 color:rgba(200,190,240,.5);text-decoration:none}
.footer{position:fixed;left:0;right:0;bottom:0;z-index:2;display:flex;
 justify-content:center;align-items:center;gap:8px;
 padding:8px 10px calc(8px + env(safe-area-inset-bottom));
 background:linear-gradient(0deg,rgba(7,3,18,.98),rgba(7,3,18,.55));border-top:1px solid rgba(124,58,237,.35);
 backdrop-filter:blur(8px)}
.footer a{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:11px;
 font-size:17px;text-decoration:none;color:#fff;transition:transform .12s,box-shadow .2s;
 box-shadow:0 0 12px rgba(124,58,237,.35)}
.footer a:active{transform:scale(.88)}
.footer .tg{background:linear-gradient(135deg,#005c8f,#0079b3);box-shadow:0 0 12px rgba(0,121,179,.45)}
.footer .yt{background:linear-gradient(135deg,#99001f,#cc0033);box-shadow:0 0 12px rgba(204,0,51,.45)}
body{padding-bottom:70px}
</style>
</head>
<body><div class='card'><div class='brand'><h1><i class='fa-solid fa-bolt'></i> HI CLIENT</h1><div class='sub'>Proxy Registration</div></div><div class='hint'>ENTER LICENSE KEY TO ACTIVATE</div><input id='key' type='text' autocomplete='off' spellcheck='false' placeholder='HI-XXXXX-XXXXX-XXXXX'><button onclick='reg()'>ACTIVATE</button><div class='actions'><button class='ghost' onclick='location.href="/getkey"'>Get Key</button></div><div id='msg' class='msg'></div><div class='hint'>After activation the proxy unlocks for your IP.<br>HI CLIENT &copy;</div><script>function reg(){var k=document.getElementById('key').value;fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k})}).then(function(r){return r.json()}).then(function(d){var m=document.getElementById('msg');m.textContent=d.msg;m.className='msg'+(d.ok?' ok':'');if(d.ok){setTimeout(function(){location.reload()},800)}})}</script></div><div class='footer'><a class='tg' href='https://t.me/+Mu9RzzeOxKphMmE1'><i class='fa-brands fa-telegram'></i></a><a class='tg' href='https://t.me/+vY8SEaLkpvEwNDJl'><i class='fa-brands fa-telegram'></i></a><a class='tg' href='https://t.me/+_EUZSOGVJj9kY2Q1'><i class='fa-brands fa-telegram'></i></a><a class='yt' href='https://youtube.com/@lunar_client_ofc?si=0C0zxCHotXF-lzat'><i class='fa-brands fa-youtube'></i></a></div></body></html>
"""

# ============================================================
#  ЛОГИРОВАНИЕ
# ============================================================
@app.before_request
def log_request():
    request._start_time = time.perf_counter()
    log.info("IN %-6s %-45s ip=%s type=%s len=%s", request.method, request.full_path.rstrip("?"), client_ip(), request.content_type, request.content_length)

@app.after_request
def log_response(response):
    started = getattr(request, "_start_time", None)
    ms = (time.perf_counter() - started) * 1000 if started else 0
    log.info("OUT %-6s %-45s status=%s type=%s len=%s %.1fms", request.method, request.path, response.status_code, response.content_type, response.calculate_content_length(), ms)
    response.headers.setdefault("Cache-Control", "no-store")
    return response

# ============================================================
#  ОСНОВНЫЕ МАРШРУТЫ
# ============================================================
@app.route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def root():
    if "text/html" not in request.headers.get("Accept", ""):
        return reverse_proxy("")
    return render_template_string(HTML)

@app.get("/panel")
def panel():
    return render_template_string(HTML)

@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": now(), "upstream": UPSTREAM_BASE_URL})

@app.post("/api/register")
def api_register():
    payload = request.get_json(silent=True) or {}
    key = str(payload.get("key", "")).strip()
    # Здесь ты можешь проверить ключ из Firebase
    # Например, сгенерировать новый ключ и сохранить в Firebase
    return jsonify({"ok": True, "msg": "Key activated! Welcome to HI CLIENT."})

@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()

    admin_role = check_admin(username, password)
    is_user = check_user(username, password) or check_legacy_user(username, password)

    if not admin_role and not is_user:
        return jsonify({"status": "error", "message": "invalid credentials"}), 401

    role = admin_role if admin_role else "user"
    sid = secrets.token_urlsafe(32)
    sessions[sid] = {
        "created_at": now(),
        "switches": dict(DEFAULT_SWITCHES),
        "role": role,
        "login": username if username else password
    }
    return jsonify({"status": "success", "session_id": sid, "role": role})

@app.post("/api/generate_key")
def generate_key():
    username = "HICLIENT-" + str(secrets.randbelow(900000) + 100000)
    password = secrets.token_urlsafe(8)
    device_id = "device_" + secrets.token_hex(4)
    payload = {
        "password": password,
        "device_id": device_id,
        "created_at": now()
    }
    requests.put(f"{FIREBASE_URL}/keys/{username}.json", json=payload)
    return jsonify({"status": "success", "username": username, "password": password})

@app.get("/api/status")
def api_status():
    sid, item, error = require_session()
    if error:
        return error
    upstream_ok = False
    try:
        r = http.get(UPSTREAM_BASE_URL, timeout=(3, 5), allow_redirects=False)
        upstream_ok = 100 <= r.status_code < 600
    except requests.RequestException:
        pass
    return jsonify({
        "status": "success",
        "client_ip": client_ip(),
        "upstream_ok": upstream_ok,
        "switches": item["switches"],
        "role": item.get("role", "user")
    })

@app.post("/api/toggle")
def api_toggle():
    sid, item, error = require_session()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", ""))
    if name not in item["switches"]:
        return jsonify({"status": "error", "message": "unknown switch"}), 400
    item["switches"][name] = not item["switches"][name]
    socketio.emit("switch_changed", {"name": name, "state": item["switches"][name]}, room=sid)
    return jsonify({"status": "success", "switches": item["switches"]})

@app.post("/api/play")
def api_play():
    sid, item, error = require_session()
    if error:
        return error
    return jsonify({"status": "success", "message": "Panel ready. Test state saved."})

# ============================================================
#  ПРОКСИ (для игровых путей)
# ============================================================
def filtered_request_headers():
    out = {}
    for key, value in request.headers.items():
        if key.lower() in HOP_BY_HOP:
            continue
        out[key] = value
    return out

def filtered_response_headers(resp: requests.Response):
    out = []
    for key, value in resp.headers.items():
        if key.lower() in HOP_BY_HOP:
            continue
        if key.lower() == "content-length":
            continue
        out.append((key, value))
    return out

@app.route("/proxy/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def reverse_proxy(path: str):
    target = urljoin(UPSTREAM_BASE_URL, path)
    raw_body = request.get_data(cache=False)
    log.info("PROXY -> %s", target)
    try:
        upstream = http.request(
            method=request.method,
            url=target,
            params=request.args,
            headers=filtered_request_headers(),
            data=raw_body if raw_body else None,
            timeout=(5, 20),
            allow_redirects=False,
            stream=True,
        )
        body = b"" if request.method == "HEAD" else upstream.raw.read(decode_content=False)
        response = Response(response=body, status=upstream.status_code, headers=filtered_response_headers(upstream))

        # ========== ПОДМЕНА verAddr ==========
        if upstream.headers.get("content-type", "").startswith("application/json"):
            try:
                import json as _json
                data = _json.loads(body)
                if isinstance(data, dict):
                    data["code"] = 0
                    if "verAddr" in data:
                        data["verAddr"] = "https://tigranxkaierproxy-production.up.railway.app/"
                        if "abhotupdate_cdn_url" in data:
                            data["abhotupdate_cdn_url"] = "https://tigranxkaierproxy-production.up.railway.app/hotpatchs/"
                        new_body = _json.dumps(data).encode("utf-8")
                        response.set_data(new_body)
                        response.headers["Content-Length"] = str(len(new_body))
            except Exception:
                pass
        # =====================================

        return response
    except requests.Timeout:
        return jsonify({"status": "error", "message": "upstream timeout", "target": target}), 504
    except requests.RequestException as exc:
        log.exception("Proxy error")
        return jsonify({"status": "error", "message": "upstream connection failed", "detail": str(exc)}), 502

# Catch-all для игровых путей
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def catch_all(path):
    if path.startswith(("panel", "api", "health", "debug", "proxy")):
        return jsonify({"error": "Not found"}), 404
    return reverse_proxy(path)

@app.route("/debug/echo", methods=["GET", "POST", "PUT", "PATCH"])
def debug_echo():
    return jsonify({"method": request.method, "path": request.path, "query": request.args.to_dict(flat=False), "content_type": request.content_type, "headers": {"user-agent": request.headers.get("User-Agent"), "accept": request.headers.get("Accept"), "authorization_present": bool(request.headers.get("Authorization"))}, "body_text": request.get_data(cache=True, as_text=True)[:2000]})

# ============================================================
#  WEBSOCKET
# ============================================================
@socketio.on("connect")
def ws_connect(auth):
    sid = ""
    if isinstance(auth, dict):
        sid = str(auth.get("session_id", "")).strip()
    item = sessions.get(sid)
    if not item:
        return False
    join_room(sid)
    emit("ready", {"status": "ok"})

# ============================================================
#  ОТВЕТ ДЛЯ ИГРЫ /ver.php (точно как LUNAR, но с твоим адресом)
# ============================================================
@app.route("/ver.php", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def ver_php():
    return jsonify({
        "code": 2,
        "use_login_optional_download": False,
        "use_background_download": False,
        "use_background_download_lobby": False,
        "country_code": "DE",
        "client_ip": "169.58.137.21",
        "gdpr_version": 1,
        "billboard_cdn_url": "",
        "billboard_msg": "",
        "web_url": "",
        "billboard_bg_url": "",
        "max_store": "",
        "max_web": "",
        "max_video": "",
        "patchnote_url": "",
        "multi_region": "",
        "appstore_url": "http://www.freefiremobile.com/",
        "backup_appstore_url": "",
        "garena_login": False,
        "garena_hint": False,
        "gop_url": "",
        "gamevar": "var_name,comment,var_type,var_value\nvar_name,comment,\"var_type float, int, bool\",var_value\nANODisabledRegions,\u5173\u95edMTP\u7684\u5730\u533a,string,\"IND,NA\"\nANODisabledClientVariant,ANODisabledClientVariant,string,\"ClientUsingVersion_MAX_HPE,ClientUsingVersion_FFI,ClientUsingVersion_MAX|IND,ClientUsingVersion_MAX|NA,ClientUsingVersion_NORMAL|NA\"\nEnableMtpLiteDataRegion,mtp\u8f7b\u7279\u5f81\u5f00\u5173,string,\"BR,EUROPE,ID,ME,US,RU,SAC,SG,TH,TW,VN,PK,ZA,BD\"\nANOEmulatorCheckDisbaledClientVariant,ANOEmulatorCheckDisbaledClientVariant,string,\"ClientUsingVersion_FFI,ClientUsingVersion_MAX,ClientUsingVersion_NORMAL\"\nForceTutorial_ChangeHudABTest,fps\u6d41\u7a0b\u4e2d\u6253\u5f00hud\u9009\u62e9\u754c\u9762\u7684\u6982\u7387,float,-1\n\nFFAntihackDefenceLevel,FFAntihackDefenceLevel,string,0,,\nFFAntihackLightInitOnThread,FFAntihackLightInitOnThread,bool,false,,\nFFAntihackEmulatorCheckDisbaledClientVariant,FFAntihackEmulatorCheckDisbaledClientVariant,string,ClientUsingVersion_FFI,ClientUsingVersion_MAX,ClientUsingVersion_NORMAL,,\nFFAntihackSDKDetailEncryptBySHA1,FFAntihackSDKDetailEncryptBySHA1,bool,false,,\nEnableFFAntihackInfoExtra,EnableFFAntihackInfoExtra,bool,false,,\nFFANTIHACKEXT_SPLIT_THRESHOLD,FFANTIHACKEXT_SPLIT_THRESHOLD,int,0,,\nDisableGinInfoSend,DisableGinInfoSend,int,1,,\nGinInfoBRAliveThreshold,GinInfoBRAliveThreshold,int,0,,\nAntiHackResetSubgameInterval,AntiHackResetSubgameInterval,int,0,,\nEnablePlatformCheck,EnablePlatformCheck,bool,false,,\nEnableSupCheck,EnableSupCheck,bool,false,,\nEnableMMKPlatformCheck,EnableMMKPlatformCheck,bool,false,,\nEnableFileInfoEncryptionAndroid,EnableFileInfoEncryptionAndroid,bool,false,,\nEnableCheckFileStates,EnableCheckFileStates,bool,false,,\nEnableNativeCheck,EnableNativeCheck,bool,false,,\nEnableSendLibs,EnableSendLibs,bool,false,,\nFFAntihackDisabledRegions,FFAntihackDisabledRegions,string,IND,BD,NA,,\nFFAntihackDisabledClientVariant,FFAntihackDisabledClientVariant,string,ClientUsingVersion_MAX_HPE,ClientUsingVersion_FFI,ClientUsingVersion_NORMAL,ClientUsingVersion_MAX|IND,ClientUsingVersion_MAX|BD,ClientUsingVersion_NORMAL|BD,,\nEnableMtpLiteDataRegion,EnableMtpLiteDataRegion,string,BR,EUROPE,ME,US,RU,SAC,SG,TH,TW,VN,PK,ZA,,\nForceTutorial_ChangeHudABTest,ForceTutorial_ChangeHudABTest,float,-1,,\nGGPUpdateFlag,GGPUpdateFlag,int,0,,\nGGPSDKPackageNameList,GGPSDKPackageNameList,string,,,\nEnableGGPDecryptFailureProtection,EnableGGPDecryptFailureProtection,bool,false,,\nEnableReplaceGGPSO,EnableReplaceGGPSO,bool,false,,\nEnableReplaceGGPSO_2022,EnableReplaceGGPSO_2022,bool,false,,\nEarlyInitGGP,EarlyInitGGP,bool,false,,\nLoadUmaIndexerAfterGGP,LoadUmaIndexerAfterGGP,bool,false,,\nGGPLoginOnce,GGPLoginOnce,bool,false,,\nEnableGGPOnLowMemory,EnableGGPOnLowMemory,bool,false,,\nEnableLobbySocialAreaStartGGP,EnableLobbySocialAreaStartGGP,bool,false,,\nEnableLobbySocialAreaSubGameGGP,EnableLobbySocialAreaSubGameGGP,bool,false,,\nRunSpeed,RunSpeed,float,3.0,,\nDashSpeedScale,DashSpeedScale,float,3.0,,",
        "device_whitelist_version": "1.6.0",
        "whitelist_mask": 0,
        "device_whitelist_sp_version": "1.0.0",
        "whitelist_sp_mask": 0,
        "ggp_url": "https://ghop-ghop.com/",
        "abhotupdate_cdn_url": "http://169.58.137.21:25565/hotpatchs/",
        "remote_version": "1.126.22",
        "version": "1.126.1",
        "app_version": "1.126.1"
    })

# ============================================================
#  ЗАПУСК
# ============================================================
if __name__ == "__main__":
    print()
    print("HI CLIENT PROXY PANEL")
    print(f"Panel:    http://127.0.0.1:{PORT}/panel")
    print(f"Health:   http://127.0.0.1:{PORT}/health")
    print(f"Upstream: {UPSTREAM_BASE_URL}")
    print()
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)