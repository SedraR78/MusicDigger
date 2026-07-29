# app/models/user_history.py
from app import db
from .base_model import BaseModel
from datetime import datetime


class UserHistory(BaseModel):
    """Mémorise les TRACKS déjà recommandés à un utilisateur.

    ⚠️ Changement par rapport à la V1 du code : l'historique portait sur les
    digs vus (dig_id). Il porte maintenant sur les tracks, parce que DigsCover
    recommande des morceaux du CATALOGUE, pas des posts existants.
    Sans ça, on ne pourrait jamais faire découvrir un son que personne n'a
    encore digé — et la feature perdrait tout son intérêt.
    """

    __tablename__ = 'user_histories'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    track_id = db.Column(db.String(36), db.ForeignKey('tracks.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'track_id', name='uq_history_user_track'),
    )

    user = db.relationship('User', back_populates='history')
    track = db.relationship('Track', back_populates='history_entries')

    @classmethod
    def mark_as_seen(cls, user_id, tracks):
        """Enregistre les tracks qu'on vient de montrer à l'utilisateur."""
        for track in tracks:
            exists = cls.query.filter_by(user_id=user_id, track_id=track.id).first()
            if not exists:
                db.session.add(cls(user_id=user_id, track_id=track.id))
        db.session.commit()

    @classmethod
    def seen_track_ids(cls, user_id):
        """Liste d'exclusion pour DigsCover.

        with_entities : on ne charge que la colonne track_id, pas les objets
        complets. Sur une liste qui peut faire des centaines de lignes, ça compte.
        """
        rows = cls.query.filter_by(user_id=user_id).with_entities(cls.track_id).all()
        return [row.track_id for row in rows]

    def __repr__(self):
        return f'<UserHistory {self.user_id} saw {self.track_id}>'
