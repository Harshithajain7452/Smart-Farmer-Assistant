"""Farmer AI chatbot (rule engine today, Gemini-ready)."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from extensions import db
from models.models import ChatbotHistory
from services.chatbot_service import QUICK_PROMPTS, generate_reply
from utils.i18n import get_locale
from utils.validators import clean_text

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot")
@login_required
def chat():
    history = (ChatbotHistory.query.filter_by(user_id=current_user.id)
               .order_by(ChatbotHistory.created_at.desc()).limit(20).all())
    return render_template("modules/chatbot.html", history=list(reversed(history)),
                           quick_prompts=QUICK_PROMPTS)


@chatbot_bp.post("/api/chat")
@login_required
def chat_api():
    payload = request.get_json(silent=True) or {}
    message = clean_text(payload.get("message"), 1000)
    if not message:
        return jsonify({"success": False, "error": "Please type a question."}), 400

    recent = (ChatbotHistory.query.filter_by(user_id=current_user.id)
              .order_by(ChatbotHistory.created_at.desc()).limit(6).all())
    history = [{"message": h.message, "response": h.response} for h in reversed(recent)]

    result = generate_reply(message, history)
    db.session.add(ChatbotHistory(user_id=current_user.id, message=message,
                                  response=result["reply"], intent=result["intent"],
                                  language=get_locale()))
    db.session.commit()
    return jsonify({"success": True, **result})


@chatbot_bp.post("/api/chat/clear")
@login_required
def clear_chat():
    ChatbotHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})
