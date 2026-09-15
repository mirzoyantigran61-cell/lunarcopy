import json
import os
from functools import wraps

import firebase_admin
from firebase_admin import auth, credentials
from flask import Blueprint, jsonify, request


account_bp = Blueprint("account_auth", __name__)

_firebase_error = None


# ============================================================
# FIREBASE ADMIN INITIALIZATION
# ============================================================

def _initialize_firebase():
    global _firebase_error

    if firebase_admin._apps:
        _firebase_error = None
        return True

    raw_credentials = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON",
        ""
    ).strip()

    if not raw_credentials:
        _firebase_error = "missing_service_account"

        print(
            "⚠️ Firebase Admin: "
            "FIREBASE_SERVICE_ACCOUNT_JSON is missing"
        )

        return False

    try:
        service_account = json.loads(
            raw_credentials
        )

        # Railway variable может быть JSON,
        # сохранённым как JSON-строка.
        if isinstance(service_account, str):
            service_account = json.loads(
                service_account
            )

        if not isinstance(
            service_account,
            dict
        ):
            raise ValueError(
                "Service account must be a JSON object"
            )

        required_fields = (
            "project_id",
            "private_key",
            "client_email"
        )

        missing_fields = [
            field
            for field in required_fields
            if not service_account.get(field)
        ]

        if missing_fields:
            raise ValueError(
                "Service account is missing required fields: "
                + ", ".join(missing_fields)
            )

        # На случай если Railway сохранил
        # переносы строк как буквальные \n.
        private_key = service_account.get(
            "private_key"
        )

        if isinstance(private_key, str):
            service_account["private_key"] = (
                private_key.replace(
                    "\\n",
                    "\n"
                )
            )

        cred = credentials.Certificate(
            service_account
        )

        firebase_admin.initialize_app(
            cred
        )

        _firebase_error = None

        print(
            "✅ Firebase Admin initialized"
        )

        return True

    except Exception as exc:
        _firebase_error = type(exc).__name__

        print(
            "❌ Firebase Admin initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )

        return False


_initialize_firebase()


# ============================================================
# FIREBASE STATUS
# ============================================================

def firebase_ready():

    if firebase_admin._apps:
        return True

    # Повторная попытка нужна, если при первом
    # импорте конфигурация была недоступна.
    return _initialize_firebase()


# ============================================================
# TOKEN HELPERS
# ============================================================

def _get_bearer_token():

    header = request.headers.get(
        "Authorization",
        ""
    ).strip()

    if not header:
        return None

    parts = header.split(
        " ",
        1
    )

    if len(parts) != 2:
        return None

    if parts[0].lower() != "bearer":
        return None

    token = parts[1].strip()

    return token or None


def verify_firebase_token():

    if not firebase_ready():

        return None, {
            "ok": False,
            "error": "firebase_not_configured"
        }

    token = _get_bearer_token()

    if not token:

        return None, {
            "ok": False,
            "error": "missing_auth_token"
        }

    try:

        decoded = auth.verify_id_token(
            token,
            check_revoked=True
        )

        return decoded, None

    except auth.ExpiredIdTokenError:

        return None, {
            "ok": False,
            "error": "token_expired"
        }

    except auth.RevokedIdTokenError:

        return None, {
            "ok": False,
            "error": "token_revoked"
        }

    except auth.UserDisabledError:

        return None, {
            "ok": False,
            "error": "user_disabled"
        }

    except auth.InvalidIdTokenError:

        return None, {
            "ok": False,
            "error": "invalid_auth_token"
        }

    except Exception as exc:

        print(
            "❌ Firebase token verification failed: "
            f"{type(exc).__name__}: {exc}"
        )

        return None, {
            "ok": False,
            "error": "authentication_failed"
        }


# ============================================================
# DECORATOR
# ============================================================

def firebase_required(view_function):

    @wraps(view_function)
    def wrapped(*args, **kwargs):

        user, error = verify_firebase_token()

        if error:

            status_code = 401

            if (
                error.get("error")
                == "firebase_not_configured"
            ):
                status_code = 503

            return jsonify(
                error
            ), status_code

        request.firebase_user = user

        return view_function(
            *args,
            **kwargs
        )

    return wrapped


# ============================================================
# CURRENT USER
# ============================================================

@account_bp.route(
    "/api/account/me",
    methods=["GET"]
)
@firebase_required
def account_me():

    user = request.firebase_user

    return jsonify({
        "ok": True,

        "user": {
            "uid": user.get("uid"),
            "email": user.get("email"),
            "name": user.get("name"),
            "picture": user.get("picture"),

            "email_verified": bool(
                user.get(
                    "email_verified",
                    False
                )
            )
        }
    }), 200


# ============================================================
# AUTH HEALTH
# ============================================================

@account_bp.route(
    "/api/account/health",
    methods=["GET"]
)
def account_health():

    ready = firebase_ready()

    result = {
        "ok": True,
        "firebase_ready": ready
    }

    # Показываем только тип проблемы,
    # никаких ключей/credentials.
    if not ready and _firebase_error:
        result["firebase_error"] = (
            _firebase_error
        )

    return jsonify(
        result
    ), 200
