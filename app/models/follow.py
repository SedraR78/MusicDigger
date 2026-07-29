# app/models/follow.py
from app import db
from .base_model import BaseModel


class Follow(BaseModel):
    __tablename__ = 'follows'

    follower_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id', name='uq_follow_pair'),
    )

    # foreign_keys est OBLIGATOIRE ici : la table a deux FK vers users,
    # SQLAlchemy ne peut pas deviner laquelle correspond à quelle relation.
    follower = db.relationship('User', foreign_keys=[follower_id],
                               back_populates='following')
    followed = db.relationship('User', foreign_keys=[followed_id],
                               back_populates='followers')

    @classmethod
    def toggle(cls, follower_id, followed_id):
        """Suit ou arrête de suivre. Retourne True si on suit maintenant."""
        # Règle métier : on ne se suit pas soi-même.
        if follower_id == followed_id:
            raise ValueError('You cannot follow yourself')

        existing = cls.query.filter_by(follower_id=follower_id,
                                       followed_id=followed_id).first()
        if existing:
            db.session.delete(existing)
            following = False
        else:
            db.session.add(cls(follower_id=follower_id, followed_id=followed_id))
            following = True

        db.session.commit()
        return following

    def __repr__(self):
        return f'<Follow {self.follower_id} → {self.followed_id}>'
