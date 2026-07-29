# app/models/message.py
from app import db
from .base_model import BaseModel


class Message(BaseModel):
    """Un message dans une conversation, avec un DIG partagé en option."""

    __tablename__ = 'messages'

    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'),
                                nullable=False)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # nullable : la plupart des messages sont du texte simple. Seuls certains
    # portent une carte DIG (comme sur le wireframe Messages).
    # C'est le lien 0..1 du diagramme ER.
    #
    #   msg_1 | "Hey, you have to listen to this" | dig_id = NULL
    #   msg_2 | "Check ça"                        | dig_id = dig_842
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=True)

    conversation = db.relationship('Conversation', back_populates='messages')
    sender = db.relationship('User', back_populates='sent_messages')
    dig = db.relationship('Dig')   # pas de back_populates : lien à sens unique

    def is_visible_to(self, user_id):
        """Un message n'est lisible que par les deux participants."""
        return self.conversation.has_participant(user_id)

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'sender': {
                'id': self.sender.id,
                'username': self.sender.display_name,
                'avatar': self.sender.avatar,
            } if self.sender else None,
            # La carte DIG intégrée dans la bulle de chat
            'shared_dig': self.dig.to_dict() if self.dig else None,
        })
        return base

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id}>'
