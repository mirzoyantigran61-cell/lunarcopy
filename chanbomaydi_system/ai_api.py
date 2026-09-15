
import os
import traceback

from flask import Blueprint, jsonify, request
from openai import OpenAI

from account_auth import firebase_required


# ============================================================
# TIGRAN AI BLUEPRINT
# ============================================================

ai_bp = Blueprint(
    "ai_api",
    __name__
)


# ============================================================
# OPENAI CONFIG
# ============================================================

OPENAI_MODEL = os.environ.get(
    "OPENAI_TEXT_MODEL",
    "gpt-5.6-sol"
).strip()


def get_openai_client():
    """
    Create OpenAI client using Railway environment variable.

    Required Railway variable:
        OPENAI_API_KEY

    Never put the API key directly in this file.
    """

    api_key = os.environ.get(
        "OPENAI_API_KEY",
        ""
    ).strip()

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key
    )


# ============================================================
# AI HEALTH CHECK
# ============================================================

@ai_bp.route(
    "/api/ai/health",
    methods=["GET"]
)
def ai_health():

    configured = bool(
        os.environ.get(
            "OPENAI_API_KEY",
            ""
        ).strip()
    )

    return jsonify({
        "ok": True,
        "configured": configured,
        "model": OPENAI_MODEL
    }), 200


# ============================================================
# TIGRAN AI CHAT
# ============================================================

@ai_bp.route(
    "/api/ai/chat",
    methods=["POST"]
)
@firebase_required
def ai_chat():

    try:

        # ----------------------------------------------------
        # Read request
        # ----------------------------------------------------

        payload = request.get_json(
            silent=True
        ) or {}

        message = str(
            payload.get(
                "message",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not message:

            return jsonify({
                "ok": False,
                "error": "empty_message"
            }), 400


        if len(message) > 12000:

            return jsonify({
                "ok": False,
                "error": "message_too_long"
            }), 400


        # ----------------------------------------------------
        # OpenAI client
        # ----------------------------------------------------

        client = get_openai_client()

        if client is None:

            return jsonify({
                "ok": False,
                "error": "openai_not_configured"
            }), 503


        # ----------------------------------------------------
        # OpenAI Responses API
        # ----------------------------------------------------

        response = client.responses.create(

            model=OPENAI_MODEL,

            instructions=(
                "You are TIGRAN AI, a helpful AI assistant. "
                "Answer clearly, accurately and naturally. "
                "Use the same language as the user unless "
                "the user asks you to use another language."
            ),

            input=message
        )


        # ----------------------------------------------------
        # Extract answer
        # ----------------------------------------------------

        answer = (
            response.output_text
            or ""
        ).strip()


        if not answer:

            return jsonify({
                "ok": False,
                "error": "empty_ai_response"
            }), 502


        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        return jsonify({
            "ok": True,
            "answer": answer,
            "model": OPENAI_MODEL
        }), 200


    except Exception:

        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": "ai_request_failed"
        }), 500
