# app/models/base_model.py
"""Classe mère de tous les models : id UUID, timestamps, save/delete/to_dict."""

from app import db
from datetime import datetime
import uuid


class BaseModel(db.Model):
    __abstract__ = True  # pas de table pour cette classe, on en hérite seulement

    # UUID plutôt qu'un entier : les DIGs ont des URL publiques, un entier
    # permettrait d'énumérer tout le contenu du site
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)  # mis à jour tout seul

    def save(self):
        """add() = met dans le caddie, commit() = passe en caisse."""
        db.session.add(self)
        db.session.commit()
        return self  # permet d'écrire Dig(...).save() en une ligne

    def delete(self):
        """⚠️ Pour un User, utiliser retire() à la place (anonymisation)."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Objet Python → dict sérialisable en JSON.

        On itère sur __table__.columns et pas sur __dict__ : après un commit,
        SQLAlchemy vide le cache de l'instance et __dict__ peut être vide.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            result[column.name] = value.isoformat() if isinstance(value, datetime) else value
        return result

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
