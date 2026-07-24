# app/models/base_model.py

from app import db
from datetime import datetime
import uuid

class BaseModel(db.Model):
    """Classe de base pour tous les modèles (comme HBNB)"""
    __abstract__ = True  # Pas de table en base de données pour cette classe
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion des kwargs (comme HBNB)"""
        if kwargs:
            # Si un id est fourni, on le garde, sinon on en génère un
            if 'id' not in kwargs:
                self.id = str(uuid.uuid4())
            
            # Gérer les dates
            if 'created_at' in kwargs and isinstance(kwargs['created_at'], str):
                kwargs['created_at'] = datetime.fromisoformat(kwargs['created_at'])
            if 'updated_at' in kwargs and isinstance(kwargs['updated_at'], str):
                kwargs['updated_at'] = datetime.fromisoformat(kwargs['updated_at'])
            
            # Assigner les attributs
            for key, value in kwargs.items():
                if key != '__class__':
                    setattr(self, key, value)
        else:
            # Si pas de kwargs, on génère un id
            self.id = str(uuid.uuid4())
    
    def save(self):
        """Sauvegarde l'objet en base (comme HBNB)"""
        self.updated_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Supprime l'objet de la base (comme HBNB)"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire (comme HBNB)"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_') and not key.startswith('sa_'):
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, list):
                    # Pour les relations, on pourrait les sérialiser plus tard
                    continue
                else:
                    result[key] = value
        return result
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
