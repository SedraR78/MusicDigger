# app/models/genre.py
from app import db
from .base_model import BaseModel


class Genre(BaseModel):
    __tablename__ = 'genres'

    # unique=True : pas deux fois "Hip-Hop" en base. La contrainte est posée
    # au niveau de la BASE, donc même un bug applicatif ne peut pas la violer.
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(10), nullable=True)  # emoji optionnel

    # Un genre regroupe plusieurs artistes et plusieurs tracks.
    # lazy='dynamic' → on récupère une requête, pas une liste : ça permet
    # .count(), .limit(), .filter() sans charger toute la table en mémoire.
    artists = db.relationship('Artist', back_populates='genre', lazy='dynamic')
    tracks = db.relationship('Track', back_populates='genre', lazy='dynamic')

    # M2M via user_favorite_genres. Le même lien lu dans l'autre sens :
    # côté User c'est user.favorite_genres, côté Genre c'est genre.fans.
    fans = db.relationship('User', secondary='user_favorite_genres',
                           back_populates='favorite_genres')

    def __repr__(self):
        return f'<Genre {self.name}>'
