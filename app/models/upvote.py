# app/models/upvote.py
from app import db
from .base_model import BaseModel


class Upvote(BaseModel):
    __tablename__ = 'upvotes'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)

    # La contrainte est posée en BASE, pas juste dans le code.
    # Pourquoi : un `if déjà upvoté` peut être contourné par une race condition
    # (deux requêtes simultanées passent le test avant qu'aucune n'ait écrit).
    # La contrainte est atomique, c'est la garantie finale.
    __table_args__ = (
        db.UniqueConstraint('user_id', 'dig_id', name='uq_upvote_user_dig'),
    )

    user = db.relationship('User', back_populates='upvotes')
    dig = db.relationship('Dig', back_populates='upvotes')

    @classmethod
    def toggle(cls, user_id, dig):
        """Ajoute ou retire l'upvote, et maintient le compteur du Dig.

        C'est le SEUL endroit du code autorisé à créer/supprimer un upvote.
        C'est ce qui garantit que dig.upvotes_count reste juste — le compteur
        dénormalisé et la table restent synchronisés parce qu'ils sont
        toujours modifiés ensemble, ici.

        Retourne (actif, nouveau_compteur) pour que la route réponde au front.
        """
        existing = cls.query.filter_by(user_id=user_id, dig_id=dig.id).first()

        if existing:
            db.session.delete(existing)
            dig.upvotes_count = max(0, dig.upvotes_count - 1)  # jamais négatif
            active = False
        else:
            db.session.add(cls(user_id=user_id, dig_id=dig.id))
            dig.upvotes_count += 1
            active = True

        db.session.commit()
        return active, dig.upvotes_count

    def __repr__(self):
        return f'<Upvote {self.user_id} → {self.dig_id}>'
