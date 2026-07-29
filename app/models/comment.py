# app/models/comment.py
from app import db
from .base_model import BaseModel


class Comment(BaseModel):
    __tablename__ = 'comments'

    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)

    # PAS de contrainte UNIQUE ici, contrairement à Upvote/Redig :
    # un utilisateur peut commenter plusieurs fois le même DIG.
    # C'est une conversation, pas un vote.

    user = db.relationship('User', back_populates='comments')
    dig = db.relationship('Dig', back_populates='comments')

    def is_owned_by(self, user_id):
        """Vérification avant suppression : on ne supprime que ses propres commentaires."""
        return self.user_id == user_id

    def to_dict(self):
        base = super().to_dict()
        base['user'] = {
            'id': self.user.id,
            'username': self.user.display_name,   # "RetiredDigger" si compte retiré
            'avatar': self.user.avatar,
        } if self.user else None
        return base

    def __repr__(self):
        return f'<Comment {self.id} on {self.dig_id}>'
