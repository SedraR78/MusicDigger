"""Messagerie privée 1-à-1.

Le point critique : vérifier que l'utilisateur fait partie de la conversation,
À L'ÉCRITURE ET À LA LECTURE. Protéger seulement l'envoi laisserait n'importe
qui lire une conversation privée en devinant son identifiant.

C'est l'un des quatre tests prioritaires du plan QA du Stage 3.
"""

from app import db
from app.models import Conversation, Message, User, Dig


class AccessDenied(Exception):
    """Levée quand un utilisateur touche à une conversation qui n'est pas la sienne."""
    pass


class MessageService:

    @staticmethod
    def start_conversation(user_id, other_username):
        """Ouvre (ou retrouve) la conversation avec un autre utilisateur."""
        other = User.query.filter_by(username=other_username).first()
        if other is None or other.is_deleted:
            raise ValueError('User not found')

        # get_or_create trie les deux ids : (A,B) et (B,A) donnent la même ligne
        return Conversation.get_or_create(user_id, other.id)

    @staticmethod
    def send_message(sender_id, conversation_id, content, dig_id=None):
        conversation = db.session.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError('Conversation not found')

        # LE contrôle d'accès. Sans lui, n'importe qui pourrait écrire dans
        # n'importe quelle conversation en devinant un identifiant.
        if not conversation.has_participant(sender_id):
            raise AccessDenied('You are not part of this conversation')

        if not content or not content.strip():
            raise ValueError('Message content is required')

        # Si un DIG est partagé, on vérifie qu'il existe vraiment
        if dig_id and db.session.get(Dig, dig_id) is None:
            raise ValueError('Shared dig not found')

        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content.strip(),
            dig_id=dig_id,
        )
        return message.save()

    @staticmethod
    def get_messages(user_id, conversation_id, since=None):
        """Lit les messages, après la même vérification.

        `since` sert au polling : le client ne redemande que les messages
        postérieurs à ce qu'il a déjà affiché.
        """
        conversation = db.session.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError('Conversation not found')

        if not conversation.has_participant(user_id):
            raise AccessDenied('You are not part of this conversation')

        query = conversation.messages
        if since:
            query = query.filter(Message.created_at > since)

        return query.order_by(Message.created_at.asc()).all()

    @staticmethod
    def list_conversations(user_id):
        """Toutes les conversations de l'utilisateur, plus récente en tête."""
        conversations = Conversation.for_user(user_id).all()

        def last_activity(conv):
            last = conv.messages.order_by(Message.created_at.desc()).first()
            return last.created_at if last else conv.created_at

        return sorted(conversations, key=last_activity, reverse=True)
