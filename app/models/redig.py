# app/models/redig.py
from app import db
from .base_model import BaseModel


class Redig(BaseModel):
    """Reposter un DIG dans son propre feed. Pèse 2× dans le score Trending."""

    __tablename__ = 'redigs'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'dig_id', name='uq_redig_user_dig'),
    )

    user = db.relationship('User', back_populates='redigs')
    dig = db.relationship('Dig', back_populates='redigs')

    @classmethod
    def toggle(cls, user_id, dig):
        """Même logique que Upvote.toggle, sur le compteur redigs_count."""
        existing = cls.query.filter_by(user_id=user_id, dig_id=dig.id).first()

        if existing:
            db.session.delete(existing)
            dig.redigs_count = max(0, dig.redigs_count - 1)
            active = False
        else:
            db.session.add(cls(user_id=user_id, dig_id=dig.id))
            dig.redigs_count += 1
            active = True

        db.session.commit()
        return active, dig.redigs_count

    def __repr__(self):
        return f'<Redig {self.user_id} → {self.dig_id}>'
