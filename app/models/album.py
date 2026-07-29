from app import db
from .base_model import BaseModel


class Album(BaseModel):
    __tablename__ = 'albums'

    # Pas de unique=True sur title : deux artistes différents peuvent avoir
    # un album du même nom ("Greatest Hits"). L'unicité porterait sur le
    # couple (title, artist_id), pas sur le titre seul.
    title = db.Column(db.String(200), nullable=False)

    artist_id = db.Column(db.String(36), db.ForeignKey('artists.id'), nullable=False)
    year = db.Column(db.Integer, nullable=True)

    # Même logique que sur Artist : on retrouve l'album par son ID Spotify
    # plutôt que par son titre, pour éviter les doublons.
    spotify_id = db.Column(db.String(100), unique=True, nullable=True)

    artist = db.relationship('Artist', back_populates='albums')
    tracks = db.relationship('Track', back_populates='album', lazy='dynamic')

    def __repr__(self):
        return f'<Album {self.title}>'
