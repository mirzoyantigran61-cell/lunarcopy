"""
License key manager.

Key format:
XXXX-XXXX-XXXX

New keys remain "pending" until first activation.
After activation the key is bound to a device and public IP.
"""

import json
import os
import secrets
import time

_BASE = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# FILE HELPERS
# ============================================================

def _path(rel):
    return os.path.join(_BASE, rel)


def _load_json(rel, default):
    p = _path(rel)

    if not os.path.exists(p):
        return default

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data is None:
            return default

        return data

    except (json.JSONDecodeError, OSError):
        return default


def _save_json(rel, data):
    p = _path(rel)
    directory = os.path.dirname(p)

    os.makedirs(directory, exist_ok=True)

    temp_path = p + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    os.replace(temp_path, p)


# ============================================================
# DATA FILES
# ============================================================

def load_ips():
    return _load_json(
        "data/allowed_ips.json",
        {}
    )


def save_ips(data):
    _save_json(
        "data/allowed_ips.json",
        data
    )


def load_license_keys():
    return _load_json(
        "data/license_keys.json",
        {}
    )


def save_license_keys(data):
    _save_json(
        "data/license_keys.json",
        data
    )


def load_db():
    return _load_json(
        "data/database.json",
        {
            "admins": {},
            "keys": {},
            "users": {}
        }
    )


def save_db(data):
    _save_json(
        "data/database.json",
        data
    )


# ============================================================
# FREEZE / MAINTENANCE
# ============================================================

def load_freeze_state():
    return _load_json(
        "data/freeze_state.json",
        {
            "frozen": False,
            "frozen_at": None
        }
    )


def is_system_frozen():
    state = load_freeze_state()
    return bool(state.get("frozen", False))


# ============================================================
# LICENSE KEY HELPERS
# ============================================================

def _rand_seg(n=4):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    return "".join(
        secrets.choice(alphabet)
        for _ in range(n)
    )


def generate_license_key():
    return (
        f"{_rand_seg()}-"
        f"{_rand_seg()}-"
        f"{_rand_seg()}"
    )


def normalize_key(value):
    if not value:
        return ""

    return "".join(
        str(value).split()
    ).upper()


def is_valid_key_format(key):
    key = normalize_key(key)

    parts = key.split("-")

    if len(parts) != 3:
        return False

    return all(
        len(part) == 4
        and part.isalnum()
        for part in parts
    )


def _now():
    return time.time()


def _get_expires_at(rec):
    try:
        return float(
            rec.get("expires_at", 0) or 0
        )
    except (TypeError, ValueError):
        return 0.0


def _is_expired(rec):
    expires = _get_expires_at(rec)

    if expires <= 0:
        return True

    return expires <= _now()


# ============================================================
# CREATE KEY
# ============================================================

def create_pending_key(
    admin_id,
    duration_type,
    days,
    cost
):
    days = int(days)

    if days <= 0:
        raise ValueError(
            "duration_days must be greater than 0"
        )

    keys = load_license_keys()

    key = generate_license_key()

    while key in keys:
        key = generate_license_key()

    keys[key] = {
        "status": "pending",
        "admin": str(admin_id),
        "duration_days": days,
        "duration_type": str(duration_type),
        "created_at": _now(),
        "cost_paid": float(cost),
        "banned": False
    }

    save_license_keys(keys)

    return key


# ============================================================
# IP BINDING
# ============================================================

def _bind_ip_to_key(
    key,
    rec,
    public_ip,
    expires
):
    public_ip = str(public_ip).strip()

    if not public_ip:
        return False, "missing_ip"

    ips = load_ips()

    old_ip = rec.get("activated_ip")
    admin = rec.get("admin")

    # --------------------------------------------------------
    # Prevent an active IP from being stolen by another key.
    # --------------------------------------------------------

    existing = ips.get(public_ip)

    if existing:
        existing_key = existing.get(
            "license_key"
        )

        try:
            existing_expiry = float(
                existing.get(
                    "expires_at",
                    0
                ) or 0
            )
        except (TypeError, ValueError):
            existing_expiry = 0

        if (
            existing_key != key
            and existing_expiry > _now()
        ):
            return False, "ip_in_use"

    # --------------------------------------------------------
    # One active IP per key.
    # --------------------------------------------------------

    stale_ips = []

    for ip, data in list(ips.items()):
        if (
            data.get("license_key") == key
            and ip != public_ip
        ):
            stale_ips.append(ip)

    for stale_ip in stale_ips:
        ips.pop(
            stale_ip,
            None
        )

    if (
        old_ip
        and old_ip != public_ip
        and old_ip in ips
        and ips[old_ip].get(
            "license_key"
        ) == key
    ):
        ips.pop(
            old_ip,
            None
        )

    # --------------------------------------------------------
    # Add current IP.
    # --------------------------------------------------------

    ips[public_ip] = {
        "expires_at": float(expires),
        "admin": admin,
        "license_key": key
    }

    save_ips(ips)

    # ========================================================
    # DATABASE
    # ========================================================

    db = load_db()

    db.setdefault(
        "admins",
        {}
    )

    db.setdefault(
        "keys",
        {}
    )

    db.setdefault(
        "users",
        {}
    )

    # --------------------------------------------------------
    # Admin key/IP list
    # --------------------------------------------------------

    if admin in db["admins"]:

        db["admins"][admin].setdefault(
            "keys",
            []
        )

        admin_keys = db["admins"][admin]["keys"]

        remove_ips = set(
            stale_ips
        )

        if (
            old_ip
            and old_ip != public_ip
        ):
            remove_ips.add(
                old_ip
            )

        admin_keys[:] = [
            item
            for item in admin_keys
            if item not in remove_ips
        ]

        if public_ip not in admin_keys:
            admin_keys.append(
                public_ip
            )

    # --------------------------------------------------------
    # Remove old IP mappings.
    # --------------------------------------------------------

    for stale_ip in stale_ips:
        db["keys"].pop(
            stale_ip,
            None
        )

    if (
        old_ip
        and old_ip != public_ip
    ):
        db["keys"].pop(
            old_ip,
            None
        )

    # --------------------------------------------------------
    # Current mapping.
    # --------------------------------------------------------

    previous = db["keys"].get(
        public_ip,
        {}
    )

    db["keys"][public_ip] = {
        "admin": admin,
        "created": previous.get(
            "created",
            _now()
        ),
        "license_key": key
    }

    save_db(db)

    return True, None


# ============================================================
# DEVICE ACTIVATION
# ============================================================

def bind_key_by_device(
    key_str,
    public_ip,
    device_token,
    telegram_user_id=None
):
    """
    Mini App activation.

    pending:
        first activation

    active:
        IP can change only when the same device token is used
    """

    key = normalize_key(
        key_str
    )

    if not is_valid_key_format(key):
        return False, "bad_format"

    device_token = str(
        device_token or ""
    ).strip()

    if not device_token:
        return False, "missing_device_token"

    public_ip = str(
        public_ip or ""
    ).strip()

    if not public_ip:
        return False, "missing_ip"

    if is_system_frozen():
        return False, "frozen"

    keys = load_license_keys()

    if key not in keys:
        return False, "not_found"

    rec = keys[key]

    # --------------------------------------------------------
    # Banned
    # --------------------------------------------------------

    if bool(
        rec.get(
            "banned",
            False
        )
    ):
        return False, "banned"

    status = str(
        rec.get(
            "status",
            ""
        )
    ).lower()

    # ========================================================
    # FIRST ACTIVATION
    # ========================================================

    if status == "pending":

        try:
            days = int(
                rec.get(
                    "duration_days",
                    0
                )
            )
        except (TypeError, ValueError):
            return False, "invalid_duration"

        if days <= 0:
            return False, "invalid_duration"

        now = _now()

        expires = (
            now
            + days * 86400
        )

        ok, err = _bind_ip_to_key(
            key,
            rec,
            public_ip,
            expires
        )

        if not ok:
            return False, err

        rec["status"] = "active"

        rec["activated_ip"] = public_ip

        rec["activated_at"] = now

        rec["expires_at"] = expires

        rec["device_token"] = device_token

        rec["device_bound_at"] = now

        rec["rebind_count"] = 0

        if telegram_user_id is not None:
            rec["telegram_user"] = str(
                telegram_user_id
            )

        keys[key] = rec

        save_license_keys(
            keys
        )

        return True, None

    # ========================================================
    # ACTIVE KEY
    # ========================================================

    if status == "active":

        if _is_expired(rec):
            return False, "expired"

        bound_device = str(
            rec.get(
                "device_token",
                ""
            ) or ""
        )

        # Device mismatch
        if (
            bound_device
            and bound_device != device_token
        ):
            return False, "device_mismatch"

        # Old key without device token:
        # migrate once.
        if not bound_device:

            rec["device_token"] = device_token

            rec["device_bound_at"] = _now()

        expires = _get_expires_at(
            rec
        )

        ok, err = _bind_ip_to_key(
            key,
            rec,
            public_ip,
            expires
        )

        if not ok:
            return False, err

        rec["activated_ip"] = public_ip

        rec["last_rebind_at"] = _now()

        rec["rebind_count"] = int(
            rec.get(
                "rebind_count",
                0
            ) or 0
        ) + 1

        if (
            telegram_user_id is not None
            and not rec.get(
                "telegram_user"
            )
        ):
            rec["telegram_user"] = str(
                telegram_user_id
            )

        keys[key] = rec

        save_license_keys(
            keys
        )

        return True, None

    return False, "already_used"


# ============================================================
# LEGACY TELEGRAM ACTIVATION
# ============================================================

def activate_license_key(
    key_str,
    public_ip,
    telegram_user_id
):
    """
    Legacy Telegram activation.

    First activation binds:
      Telegram user
      Public IP
      Expiration time
    """

    key = normalize_key(
        key_str
    )

    if not is_valid_key_format(key):
        return False, "bad_format"

    public_ip = str(
        public_ip or ""
    ).strip()

    if not public_ip:
        return False, "missing_ip"

    if is_system_frozen():
        return False, "frozen"

    keys = load_license_keys()

    if key not in keys:
        return False, "not_found"

    rec = keys[key]

    if bool(
        rec.get(
            "banned",
            False
        )
    ):
        return False, "banned"

    user_id = str(
        telegram_user_id
    )

    status = str(
        rec.get(
            "status",
            ""
        )
    ).lower()

    # ========================================================
    # EXISTING ACTIVE KEY
    # ========================================================

    if status == "active":

        owner = str(
            rec.get(
                "telegram_user",
                ""
            )
        )

        if owner != user_id:
            return False, "already_used"

        if _is_expired(rec):
            return False, "expired"

        expires = _get_expires_at(
            rec
        )

        ok, err = _bind_ip_to_key(
            key,
            rec,
            public_ip,
            expires
        )

        if not ok:
            return False, err

        rec["activated_ip"] = public_ip

        rec["last_rebind_at"] = _now()

        rec["rebind_count"] = int(
            rec.get(
                "rebind_count",
                0
            ) or 0
        ) + 1

        keys[key] = rec

        save_license_keys(
            keys
        )

        return True, None

    # ========================================================
    # NOT PENDING
    # ========================================================

    if status != "pending":
        return False, "already_used"

    # ========================================================
    # FIRST ACTIVATION
    # ========================================================

    try:
        days = int(
            rec.get(
                "duration_days",
                0
            )
        )
    except (TypeError, ValueError):
        return False, "invalid_duration"

    if days <= 0:
        return False, "invalid_duration"

    now = _now()

    expires = (
        now
        + days * 86400
    )

    ok, err = _bind_ip_to_key(
        key,
        rec,
        public_ip,
        expires
    )

    if not ok:
        return False, err

    rec["status"] = "active"

    rec["activated_ip"] = public_ip

    rec["activated_at"] = now

    rec["expires_at"] = expires

    rec["telegram_user"] = user_id

    rec["rebind_count"] = 0

    keys[key] = rec

    save_license_keys(
        keys
    )

    return True, None
