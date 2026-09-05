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

# ===== AES =====
from Crypto.Cipher import AES
from Crypto.Util import Counter
import base64

PORT = int(os.environ.get("PORT", "8080"))
UPSTREAM_BASE_URL = os.environ.get("UPSTREAM_BASE_URL", "http://127.0.0.1:9000").rstrip("/") + "/"
SESSION_TTL = int(os.environ.get("SESSION_TTL", str(12 * 60 * 60)))

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
#  ПРОВЕРКА АДМИНА / КЛЮЧА
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
#  HTML-ИНТЕРФЕЙС (HI PROXY + ГЕНЕРАТОР)
# ============================================================
HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a0710">
<title>HI PROXY Panel</title>
<style>
:root{--bg:#08060d;--bg2:#10091b;--card:rgba(18,12,30,.78);--card2:rgba(25,13,43,.88);--purple:#b45cff;--purple2:#7d28ff;--pink:#f05cff;--cyan:#78f7ff;--ok:#79ffbc;--muted:rgba(255,255,255,.46);--line:rgba(198,116,255,.18);--shadow:0 0 26px rgba(180,92,255,.17)}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:#fff}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:radial-gradient(900px 700px at 10% 18%,rgba(142,49,255,.18),transparent 58%),radial-gradient(700px 500px at 96% 72%,rgba(241,72,255,.10),transparent 54%),linear-gradient(180deg,#08060d,#0c0712 42%,#06050a);overflow-x:hidden}
body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.16;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:32px 32px;mask-image:linear-gradient(to bottom,#000,transparent 92%)}
.app{width:min(100%,470px);margin:0 auto;padding:18px 15px 34px}
.topbar{display:flex;align-items:center;justify-content:space-between;margin:4px 2px 20px}
.brand{display:flex;align-items:center;gap:10px;font-size:12px;letter-spacing:3px;font-weight:900}
.bolt{font-size:22px;color:var(--purple);filter:drop-shadow(0 0 12px var(--purple))}
.version{border:1px solid var(--line);padding:8px 12px;border-radius:12px;color:#ddd;font:700 11px ui-monospace,SFMono-Regular,Menlo,monospace;background:rgba(255,255,255,.02)}
.locked{display:flex;gap:9px;align-items:center;justify-content:center;color:#c996ff;font:800 12px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:3px;text-transform:uppercase;margin:8px 0 8px}
.dot{width:9px;height:9px;border-radius:50%;background:var(--ok);box-shadow:0 0 18px var(--ok)}
h1{margin:0;text-align:center;font:900 clamp(30px,9vw,42px) ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:2px;background:linear-gradient(90deg,#fff 4%,#d9b6ff 34%,#a75aff 66%,#fff 96%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 14px rgba(182,90,255,.46))}
.subtitle{text-align:center;color:var(--muted);font:700 10px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:3px;line-height:1.7;margin:9px 0 22px;text-transform:uppercase}
.card{position:relative;overflow:hidden;background:linear-gradient(145deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:28px;padding:22px;margin:0 0 14px;box-shadow:0 18px 55px rgba(0,0,0,.42),var(--shadow)}
.card:after{content:"";position:absolute;width:160px;height:160px;right:-75px;top:-85px;border-radius:50%;background:radial-gradient(circle,rgba(184,91,255,.17),transparent 66%);pointer-events:none}
.card-title{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:15px}
.card-title h2{font-size:24px;margin:0;letter-spacing:.2px}
.check{width:58px;height:58px;border:1px solid rgba(198,116,255,.25);border-radius:18px;display:grid;place-items:center;background:rgba(170,72,255,.08);box-shadow:inset 0 0 25px rgba(183,91,255,.08)}
.check span{font-size:30px;color:var(--ok);filter:drop-shadow(0 0 10px var(--ok))}
.statusline{display:flex;align-items:center;gap:10px;color:var(--ok);font-weight:900;letter-spacing:2px;font-size:12px;margin:4px 0 17px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.stat{min-height:100px;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.025);border-radius:18px;padding:15px;display:flex;flex-direction:column;justify-content:center}
.stat.wide{grid-column:span 2;min-height:84px}
.k{color:rgba(255,255,255,.35);font:800 10px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:2px}
.v{margin-top:9px;color:var(--ok);font:900 17px ui-monospace,SFMono-Regular,Menlo,monospace;text-shadow:0 0 14px rgba(121,255,188,.26);overflow-wrap:anywhere}
.active-strip{margin:12px 0 8px;padding:12px 14px;border-radius:15px;border:1px solid rgba(199,111,255,.17);background:linear-gradient(90deg,rgba(177,77,255,.06),rgba(230,88,255,.05));display:flex;justify-content:space-between;gap:16px;align-items:center;font:800 10px ui-monospace,SFMono-Regular,Menlo,monospace;color:rgba(255,255,255,.39);letter-spacing:1.2px}
#activeText{color:#d9b2ff;text-align:right}
.switches{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.switch-row{min-height:66px;border:1px solid rgba(255,255,255,.06);border-radius:17px;padding:10px 11px;background:rgba(255,255,255,.025);display:flex;align-items:center;justify-content:space-between;gap:10px;transition:.25s ease;position:relative;overflow:hidden}
.switch-row.flash:before{content:"";position:absolute;inset:-80%;background:conic-gradient(transparent,rgba(207,123,255,.5),transparent 20%);animation:spin .7s linear}
@keyframes spin{to{transform:rotate(360deg)}}
.switch-label{font-size:12px;font-weight:800;position:relative;z-index:1}
.toggle{position:relative;width:54px;height:30px;border-radius:99px;background:#292134;border:1px solid rgba(255,255,255,.08);box-shadow:inset 0 2px 8px rgba(0,0,0,.35);cursor:pointer;transition:.25s;flex:0 0 auto;z-index:1}
.toggle:after{content:"";position:absolute;width:24px;height:24px;left:2px;top:2px;border-radius:50%;background:#8d8796;box-shadow:0 3px 8px rgba(0,0,0,.45);transition:.25s}
.toggle.on{background:linear-gradient(90deg,#7d28ff,#cb5dff);box-shadow:0 0 22px rgba(182,81,255,.45),inset 0 0 12px rgba(255,255,255,.18)}
.toggle.on:after{transform:translateX(24px);background:#fff;box-shadow:0 0 16px rgba(255,255,255,.85)}
.hint{text-align:center;color:rgba(255,255,255,.27);font:700 10px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1px;margin:18px 0 12px}
.play{width:100%;border:1px solid rgba(209,122,255,.28);border-radius:22px;padding:17px;background:linear-gradient(90deg,rgba(109,27,255,.22),rgba(236,70,255,.14));color:#fff;font:900 15px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:4px;box-shadow:0 0 24px rgba(177,67,255,.15),inset 0 0 20px rgba(255,255,255,.04);cursor:pointer;transition:.18s}
.play:active{transform:scale(.985)}
.login{margin-top:18px;padding:22px;border:1px solid var(--line);border-radius:24px;background:rgba(20,12,32,.76);box-shadow:var(--shadow)}
.login input{width:100%;padding:16px;border-radius:15px;border:1px solid rgba(202,120,255,.22);background:#0c0911;color:#fff;outline:none;text-align:center;font-size:15px;letter-spacing:1px;margin-bottom:10px}
.login button{width:100%;margin-top:11px;padding:15px;border:0;border-radius:15px;cursor:pointer;background:linear-gradient(90deg,#7f2bff,#cf5fff);color:#fff;font-weight:900;letter-spacing:1px;box-shadow:0 0 24px rgba(175,76,255,.25)}
.btn-secondary{width:100%;margin-top:10px;padding:14px;border:1px solid var(--line);border-radius:15px;background:transparent;color:#fff;font-weight:800;cursor:pointer;}
.msg{min-height:20px;text-align:center;margin-top:10px;font-size:12px;color:#ff91c7}
.footer{text-align:center;color:rgba(255,255,255,.18);font:700 9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:2px;margin-top:18px}
.hidden{display:none!important}
.toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,20px);opacity:0;background:#16101e;border:1px solid var(--line);border-radius:14px;padding:12px 16px;z-index:99;box-shadow:0 15px 50px rgba(0,0,0,.55),0 0 25px rgba(176,77,255,.24);transition:.22s;font-size:12px;max-width:calc(100vw - 30px);text-align:center}
.toast.show{opacity:1;transform:translate(-50%,0)}
@media(max-width:370px){.switches{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.stat.wide{grid-column:span 1}}
</style>
</head>
<body>
<div class="app">
  <div class="topbar"><div class="brand"><span class="bolt">⚡</span> HI / PROXY</div><div class="version">V1.0</div></div>
  <div class="locked"><span class="dot"></span> SYSTEM READY</div>
  <h1>HI PROXY</h1>
  <div class="subtitle">Secure access gateway · protocol-safe pass-through</div>

  <!-- ЛОГИН -->
  <section id="loginBox" class="login">
    <input id="username" autocomplete="off" placeholder="Enter USERNAME">
    <input id="password" type="password" autocomplete="off" placeholder="Enter PASSWORD">
    <button onclick="login()">UNLOCK ACCESS</button>
    <button onclick="showGenerator()" class="btn-secondary">GENERATE KEY</button>
    <div class="msg" id="msg"></div>
  </section>

  <!-- ЭКРАН ГЕНЕРАТОРА -->
  <section id="generatorBox" class="login hidden">
    <h2 style="text-align:center;">Key Generator</h2>
    <p style="text-align:center; font-size:14px; color:var(--muted);">Get a fresh key in 15 seconds.</p>
    <button onclick="goToExternal()" class="play" style="margin-top:20px;">GENERATE KEY</button>
    <button onclick="showLogin()" class="btn-secondary">← BACK</button>
  </section>

  <!-- ЭКРАН ВЕРИФИКАЦИИ (ТАЙМЕР) -->
  <section id="verificationBox" class="login hidden">
    <h2 style="text-align:center;">Verifying...</h2>
    <div id="timer" style="text-align:center; font-size:32px; font-weight:900; margin:20px 0;">15</div>
    <p style="text-align:center; color:var(--muted);">Please wait...</p>
  </section>

  <!-- ЭКРАН РЕЗУЛЬТАТА -->
  <section id="keyResultBox" class="login hidden">
    <h2 style="text-align:center;">Your Key</h2>
    <div style="margin:15px 0; padding:15px; background:rgba(255,255,255,0.05); border-radius:12px;">
      <div style="font-size:13px; color:var(--muted);">USERNAME</div>
      <div id="generatedUsername" style="font-size:20px; font-weight:800; margin-bottom:10px;"></div>
      <div style="font-size:13px; color:var(--muted);">PASSWORD</div>
      <div id="generatedPassword" style="font-size:20px; font-weight:800;"></div>
    </div>
    <button onclick="copyKey()" class="play">📋 COPY KEY</button>
    <button onclick="showLogin()" class="btn-secondary">LOGIN</button>
  </section>

  <!-- ПАНЕЛЬ -->
  <main id="panel" class="hidden">
    <section class="card">
      <div class="card-title"><div><h2>Access active</h2><div class="subtitle" style="text-align:left;margin:4px 0 0">CONTROL PANEL</div></div><div class="check"><span>✓</span></div></div>
      <div class="statusline"><span class="dot"></span> ACCESS ACTIVE</div>
      <div class="grid">
        <div class="stat"><div class="k">STATUS</div><div class="v" id="statusValue">ACTIVE</div></div>
        <div class="stat"><div class="k">UPSTREAM</div><div class="v" id="upstreamValue">CHECKING</div></div>
        <div class="stat wide"><div class="k">YOUR IP</div><div class="v" id="ipValue">—</div></div>
      </div>
      <div class="active-strip"><span>ACTIVE MODES</span><span id="activeText">NONE</span></div>
      <div class="switches" id="switches"></div>
      <div class="hint">Settings auto-save in this panel session.</div>
      <button class="play" onclick="play()">♫ &nbsp; PLAY</button>
    </section>
  </main>

  <div class="footer">HI PROXY · AUTHORIZED TEST ENVIRONMENTS ONLY</div>
</div>
<div id="toast" class="toast"></div>

<script>
let sessionId = localStorage.getItem("hi_session") || "";
let state = {};

function toast(text){
  const t = document.getElementById("toast");
  t.textContent = text;
  t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"), 1700);
}

async function api(path, options={}){
  options.headers = options.headers || {};
  if(sessionId) options.headers["X-Session-ID"] = sessionId;
  const r = await fetch(path, options);
  let data = {};
  try { data = await r.json(); } catch(e) {}
  if(r.status === 401){
    localStorage.removeItem("hi_session");
    sessionId = "";
    showLogin();
    throw new Error("Session expired");
  }
  if(!r.ok) throw new Error(data.message || ("HTTP " + r.status));
  return data;
}

async function login(){
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const msg = document.getElementById("msg");
  if(!password){msg.textContent="Enter password.";return;}
  try{
    const data = await api("/api/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username, password})});
    sessionId = data.session_id;
    localStorage.setItem("hi_session", sessionId);
    msg.textContent="";
    showPanel();
    await refresh();
  }catch(e){msg.textContent=e.message;}
}

function showLogin(){
  document.getElementById("generatorBox").classList.add("hidden");
  document.getElementById("verificationBox").classList.add("hidden");
  document.getElementById("keyResultBox").classList.add("hidden");
  document.getElementById("loginBox").classList.remove("hidden");
}

function showGenerator(){
  document.getElementById("loginBox").classList.add("hidden");
  document.getElementById("generatorBox").classList.remove("hidden");
}

function goToExternal(){
  const externalUrl = "https://vplink.in/eoKVQ";
  window.open(externalUrl, "_blank");
  setTimeout(() => { showVerification(); }, 1000);
}

function showVerification(){
  document.getElementById("generatorBox").classList.add("hidden");
  document.getElementById("verificationBox").classList.remove("hidden");
  let count = 15;
  const timerEl = document.getElementById("timer");
  timerEl.textContent = count;
  const interval = setInterval(() => {
    count--;
    timerEl.textContent = count;
    if (count <= 0) {
      clearInterval(interval);
      generateKey();
    }
  }, 1000);
}

async function generateKey(){
  try {
    const res = await fetch("/api/generate_key", { method: "POST" });
    const data = await res.json();
    if (data.status === "success") {
      document.getElementById("verificationBox").classList.add("hidden");
      document.getElementById("keyResultBox").classList.remove("hidden");
      document.getElementById("generatedUsername").textContent = data.username;
      document.getElementById("generatedPassword").textContent = data.password;
      localStorage.setItem("temp_username", data.username);
      localStorage.setItem("temp_password", data.password);
    } else {
      alert("Error generating key");
    }
  } catch(e) {
    alert("Server error");
  }
}

function copyKey(){
  const username = document.getElementById("generatedUsername").textContent;
  const password = document.getElementById("generatedPassword").textContent;
  const text = `Username: ${username}\nPassword: ${password}`;
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById("username").value = username;
    document.getElementById("password").value = password;
    showLogin();
  });
}

function showPanel(){
  document.getElementById("loginBox").classList.add("hidden");
  document.getElementById("generatorBox").classList.add("hidden");
  document.getElementById("verificationBox").classList.add("hidden");
  document.getElementById("keyResultBox").classList.add("hidden");
  document.getElementById("panel").classList.remove("hidden");
}

function renderSwitches(){
  const box = document.getElementById("switches");
  box.innerHTML="";
  Object.keys(state).forEach(name=>{
    const row=document.createElement("div");
    row.className="switch-row";
    const label=document.createElement("div");
    label.className="switch-label";
    label.textContent=name;
    const toggle=document.createElement("div");
    toggle.className="toggle " + (state[name] ? "on" : "");
    toggle.onclick=async()=>{
      row.classList.remove("flash");
      void row.offsetWidth;
      row.classList.add("flash");
      try{
        const data = await api("/api/toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name})});
        state = data.switches;
        renderSwitches();
        updateActive();
        toast(name + ": " + (state[name] ? "ON" : "OFF"));
      }catch(e){toast(e.message);}
    };
    row.append(label,toggle);
    box.appendChild(row);
  });
}

function updateActive(){
  const active=Object.entries(state).filter(([,v])=>v).map(([k])=>k.toUpperCase());
  document.getElementById("activeText").textContent=active.length ? active.join(" + ") : "NONE";
}

async function refresh(){
  const data=await api("/api/status");
  state=data.switches || {};
  document.getElementById("ipValue").textContent=data.client_ip || "—";
  document.getElementById("upstreamValue").textContent=data.upstream_ok ? "ONLINE" : "OFFLINE";
  document.getElementById("statusValue").textContent="ACTIVE";
  renderSwitches();
  updateActive();
}

async function play(){
  try{
    const data=await api("/api/play",{method:"POST"});
    toast(data.message);
  }catch(e){toast(e.message);}
}

document.getElementById("password").addEventListener("keydown",e=>{
  if(e.key==="Enter") login();
});

(async()=>{
  if(!sessionId){showLogin();return;}
  try{showPanel();await refresh();}catch(e){showLogin();}
})();
</script>
</body>
</html>
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
    return redirect("/panel", code=302)



@app.get("/panel")
def panel():
    return render_template_string(HTML)

@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": now(), "upstream": UPSTREAM_BASE_URL})

# ===== ДОБАВЬ ЭТО ПОСЛЕ health =====
@app.route('/ver.php', methods=['GET'])
def ver_php():
    return jsonify({
        "code": 0,
        "version": "1.130.22",
        "message": "OK",
        "verAddr": "https://lunarcopy-production.up.railway.app/",
        "abhotupdate_cdn_url": "https://lunarcopy-production.up.railway.app/hotpatchs/"
    })
    
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
    username = "HIPROXYSERVER-" + str(secrets.randbelow(900000) + 100000)
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

        return response
    except requests.Timeout:
        return jsonify({"status": "error", "message": "upstream timeout", "target": target}), 504
    except requests.RequestException as exc:
        log.exception("Proxy error")
        return jsonify({"status": "error", "message": "upstream connection failed", "detail": str(exc)}), 502

@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def catch_all(path):
    if path.startswith(("panel", "api", "health", "debug", "proxy")):
        return jsonify({"error": "Not found"}), 404
    return reverse_proxy(path)

@app.route("/debug/echo", methods=["GET", "POST", "PUT", "PATCH"])
def debug_echo():
    return jsonify({"method": request.method, "path": request.path, "query": request.args.to_dict(flat=False), "content_type": request.content_type, "headers": {"user-agent": request.headers.get("User-Agent"), "accept": request.headers.get("Accept"), "authorization_present": bool(request.headers.get("Authorization"))}, "body_text": request.get_data(cache=True, as_text=True)[:2000]})

# ============================================================
#  НОВЫЙ ENDPOINT ДЛЯ СКАЧИВАНИЯ .SO (ШИФРОВАННЫЙ)
# ============================================================
AES_KEY = b'0123456789abcdef'  # 16 байт, смени!
AES_IV = b'fedcba9876543210'  # 16 байт, смени!

@app.route('/api/get_lib', methods=['GET'])
def get_lib():
    lib_path = 'libPrabirxLive.so'
    try:
        with open(lib_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "lib not found"}), 404

    counter = Counter.new(128, initial_value=int.from_bytes(AES_IV, 'big'))
    cipher = AES.new(AES_KEY, AES.MODE_CTR, counter=counter)
    encrypted_data = cipher.encrypt(data)

    return base64.b64encode(encrypted_data).decode('utf-8')

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
#  ЗАПУСК
# ============================================================
if __name__ == "__main__":
    print()
    print("HI PROXY PANEL")
    print(f"Panel:    http://127.0.0.1:{PORT}/panel")
    print(f"Health:   http://127.0.0.1:{PORT}/health")
    print(f"Upstream: {UPSTREAM_BASE_URL}")
    print()
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)
