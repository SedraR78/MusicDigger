"""Routes de la messagerie.

Le service lève des exceptions métier (ValueError, AccessDenied) sans jamais
connaître HTTP. C'est la route qui les traduit en codes :
    conversation inexistante → 404
    pas participant          → 403
    contenu vide             → 400
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.message_service import MessageService, AccessDenied

message_bp = Blueprint('messages', __name__)


def error(message, code):
    return jsonify({'error': message, 'code': code}), code


# ============================================================
# CONVERSATIONS
# ============================================================

@message_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    """GET /api/conversations — la colonne de gauche de l'écran Messages."""
    user_id = get_jwt_identity()
    conversations = MessageService.list_conversations(user_id)

    return jsonify({
        'conversations': [c.to_dict(current_user_id=user_id)
                          for c in conversations],
    }), 200


@message_bp.route('/conversations', methods=['POST'])
@jwt_required()
def start_conversation():
    """POST /api/conversations {username}

    Idempotent : si la conversation existe déjà, on la renvoie au lieu d'en
    créer une seconde (grâce à l'ordre canonique des identifiants).
    """
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()

    if not username:
        return error('username is required', 400)

    user_id = get_jwt_identity()

    try:
        conversation = MessageService.start_conversation(user_id, username)
    except ValueError as exc:
        return error(str(exc), 404 if 'not found' in str(exc) else 400)

    return jsonify({
        'conversation': conversation.to_dict(current_user_id=user_id),
    }), 200


# ============================================================
# MESSAGES
# ============================================================

@message_bp.route('/conversations/<conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """GET /api/conversations/<id>/messages?since=ISO8601

    Le paramètre `since` alimente le polling : le front redemande toutes les
    quelques secondes, mais ne reçoit que les nouveaux messages. Pas de
    WebSockets dans le MVP — plus simple à déployer et suffisant ici.
    """
    user_id = get_jwt_identity()
    since_raw = request.args.get('since')

    since = None
    if since_raw:
        try:
            since = datetime.fromisoformat(since_raw)
        except ValueError:
            return error('since must be an ISO 8601 datetime', 400)

    try:
        messages = MessageService.get_messages(user_id, conversation_id, since)
    except AccessDenied as exc:
        return error(str(exc), 403)
    except ValueError as exc:
        return error(str(exc), 404)

    return jsonify({'messages': [m.to_dict() for m in messages]}), 200


@message_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    """POST /api/messages {conversation_id, content, dig_id?}

    dig_id est optionnel : la plupart des messages sont du texte simple, seuls
    certains portent une carte DIG partagée (le lien 0..1 de l'ER).
    """
    data = request.get_json(silent=True) or {}
    conversation_id = data.get('conversation_id')

    if not conversation_id:
        return error('conversation_id is required', 400)

    try:
        message = MessageService.send_message(
            sender_id=get_jwt_identity(),
            conversation_id=conversation_id,
            content=data.get('content'),
            dig_id=data.get('dig_id'),
        )
    except AccessDenied as exc:
        return error(str(exc), 403)
    except ValueError as exc:
        return error(str(exc), 404 if 'not found' in str(exc) else 400)

    return jsonify({'message': message.to_dict()}), 201
