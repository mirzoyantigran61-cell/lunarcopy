
import json
import os
from functools import wraps

import firebase_admin
from firebase_admin import auth, credentials
from flask import Blueprint, jsonify, request


account_bp = Blueprint("account_auth", __name__)


# ============================================================
# FIREBASE ADMIN INITIALIZATION
# ============================================================

def _initialize_firebase():
    """
    Firebase Admin запускается один раз.

    Railway variable:
        FIREBASE_SERVICE_ACCOUNT_JSON

    Значение переменной = полный JSON Service Account.
    Сам JSON НЕ нужно сохранять в GitHub.
    """

    if firebase_admin._apps:
        return

    raw_credentials = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON",
        ""
    ).strip()

    if not raw_credentials:
        print(
            "⚠️ FIREBASE_SERVICE_ACCOUNT_JSON is not configured"
        )
        return

    try:
        service_account = json.loads(
            raw_credentials
        )

        cred = credentials.Certificate(
            service_account
        )

        firebase_admin.initialize_app(
            cred
        )

        print(
            "✅ Firebase Admin initialized"
        )

    except Exception as exc:
        print(
            f"❌ Firebase initialization error: {exc}"
        )


_initialize_firebase()


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

    if not firebase_admin._apps:

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

        # check_revoked=True также не принимает
        # отозванные Firebase-сессии.
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
            f"❌ Firebase token verification error: {exc}"
        )

        return None, {
            "ok": False,
            "error": "authentication_failed"
        }


# ============================================================
# DECORATOR FOR PROTECTED API
# ============================================================

def firebase_required(view_function):

    @wraps(view_function)
    def wrapped(*args, **kwargs):

        user, error = verify_firebase_token()

        if error:

            return jsonify(
                error
            ), 401

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
            "uid": user.get(
                "uid"
            ),

            "email": user.get(
                "email"
            ),

            "name": user.get(
                "name"
            ),

            "picture": user.get(
                "picture"
            ),

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

    return jsonify({
        "ok": True,
        "firebase_ready": bool(
            firebase_admin._apps
        )
    }), 200
