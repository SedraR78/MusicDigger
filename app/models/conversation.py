# app/models/conversation.py
from app import db
from .base_model import BaseModel


class Conversation(BaseModel):
    """Conversation privée entre exactement deux utilisateurs.

    Le problème : si Sedra écrit à Julie puis Julie à Sedra, il ne doit pas y
    avoir DEUX conversations. Or (sedra, julie) et (julie, sedra) sont deux
    paires différentes pour la base.

    La solution : l'ORDRE CANONIQUE. On trie toujours les deux ids avant de
    stocker, donc user1_id est toujours le plus petit. La paire est écrite
    de la même façon dans les deux sens, et la contrainte UNIQUE fonctionne.

    Métaphore : ranger les noms d'un couple par ordre alphabétique sur une
    boîte aux lettres — "Dupont-Martin", peu importe qui est arrivé en premier.
    """

    __tablename__ = 'conversations'

    user1_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='uq_conversation_pair'),
    )

    # foreign_keys obligatoire : deux FK vers users dans la même table
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])

    messages = db.relationship('Message', back_populates='conversation',
                               lazy='dynamic', cascade='all, delete-orphan')

    @classmethod
    def get_or_create(cls, user_a_id, user_b_id):
        """Récupère la conversation entre deux users, ou la crée."""
        if user_a_id == user_b_id:
            raise ValueError('You cannot start a conversation with yourself')

        first, second = sorted([user_a_id, user_b_id])   # l'ordre canonique

        conversation = cls.query.filter_by(user1_id=first, user2_id=second).first()
        if conversation is None:
            conversation = cls(user1_id=first, user2_id=second)
            db.session.add(conversation)
            db.session.commit()
        return conversation

    def has_participant(self, user_id):
        """LE contrôle d'accès de la messagerie.

        Appelé à l'écriture ET à la lecture. Protéger seulement l'envoi
        laisserait n'importe qui lire une conversation privée en devinant
        son identifiant.
        """
        return user_id in (self.user1_id, self.user2_id)

    def other_user(self, user_id):
        """L'interlocuteur, du point de vue de user_id."""
        return self.user2 if self.user1_id == user_id else self.user1

    @classmethod
    def for_user(cls, user_id):
        """Toutes les conversations d'un user, quel que soit son rôle (1 ou 2)."""
        return cls.query.filter(
            db.or_(cls.user1_id == user_id, cls.user2_id == user_id)
        )

    def to_dict(self, current_user_id=None):
        # Import local : Message importe Conversation, donc un import en haut
        # de fichier créerait une boucle.
        from .message import Message

        base = super().to_dict()
        last = self.messages.order_by(Message.created_at.desc()).first()
        base.update({
            'last_message': last.to_dict() if last else None,
            'other_user': self.other_user(current_user_id).to_dict()
                          if current_user_id else None,
        })
        return base

    def __repr__(self):
        return f'<Conversation {self.user1_id} ↔ {self.user2_id}>'
