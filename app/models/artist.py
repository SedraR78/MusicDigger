from app import db
from .base_model import BaseModel


class Artist(BaseModel):
    __tablename__ = 'artists'

    name = db.Column(db.String(200), unique=True, nullable=False)

    # nullable : Spotify ne renvoie pas toujours de genre pour un artiste
    genre_id = db.Column(db.String(36), db.ForeignKey('genres.id'), nullable=True)

    # Évite les doublons quand deux artistes ont le même nom, et permet
    # de recharger ses genres sans le rechercher par nom.
    spotify_id = db.Column(db.String(100), unique=True, nullable=True)

    genre = db.relationship('Genre', back_populates='artists')
    tracks = db.relationship('Track', back_populates='artist', lazy='dynamic')
    albums = db.relationship('Album', back_populates='artist', lazy='dynamic')
    fans = db.relationship('User', secondary='user_favorite_artists',
                           back_populates='favorite_artists')

    def __repr__(self):
        return f'<Artist {self.name}>'
