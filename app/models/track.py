from app import db
from .base_model import BaseModel


class Track(BaseModel):
    """Un morceau du catalogue, mis en cache depuis Spotify ou YouTube.

    Pourquoi on stocke au lieu d'appeler l'API à chaque fois :
      1. vitesse — 1 ms en local contre ~200 ms chez Spotify
      2. quotas — les APIs limitent le nombre d'appels
      3. résilience — si Spotify tombe, l'app continue sur le cache
    """

    __tablename__ = 'tracks'

    title = db.Column(db.String(200), nullable=False)

    artist_id = db.Column(db.String(36), db.ForeignKey('artists.id'), nullable=False)
    album_id = db.Column(db.String(36), db.ForeignKey('albums.id'), nullable=True)
    genre_id = db.Column(db.String(36), db.ForeignKey('genres.id'), nullable=True)

    # Un seul des deux est rempli selon la source. unique=True empêche
    # de mettre deux fois le même morceau en cache.
    spotify_id = db.Column(db.String(100), unique=True, nullable=True)
    youtube_id = db.Column(db.String(100), unique=True, nullable=True)

    cover_url = db.Column(db.String(300), nullable=True)    # pochette
    preview_url = db.Column(db.String(300), nullable=True)  # extrait 30s (Spotify)
    embed_url = db.Column(db.String(300), nullable=True)    # le player ▶
    duration_ms = db.Column(db.Integer, nullable=True)
    popularity = db.Column(db.Integer, nullable=True)

    artist = db.relationship('Artist', back_populates='tracks')
    album = db.relationship('Album', back_populates='tracks')
    genre = db.relationship('Genre', back_populates='tracks')
    digs = db.relationship('Dig', back_populates='track', lazy='dynamic')
    fans = db.relationship('User', secondary='user_favorite_tracks',
                           back_populates='favorite_tracks')

    # L'historique DigsCover porte sur les TRACKS (pas les digs) : c'est ce
    # qui permet de ne jamais reproposer un morceau déjà montré.
    history_entries = db.relationship('UserHistory', back_populates='track',
                                      lazy='dynamic')

    @property
    def digs_count(self):
        """Nombre de DIGs postés à propos de ce morceau.

        .count() fonctionne parce que la relation est lazy='dynamic'
        (elle renvoie une requête). Sur une liste Python, ça planterait.
        """
        return self.digs.count()

    def share_url(self):
        return f'/tracks/{self.id}'

    def to_dict(self):
        base = super().to_dict()
        # On renvoie les NOMS, pas les objets complets : si on appelait
        # artist.to_dict() qui sérialise ses tracks qui sérialisent leur
        # artiste... récursion infinie. Piège classique des ORM.
        base.update({
            'artist': self.artist.name if self.artist else None,
            'album': self.album.title if self.album else None,
            'genre': self.genre.name if self.genre else None,
            'digs_count': self.digs_count,
            'share_url': self.share_url(),
        })
        return base

    def __repr__(self):
        return f'<Track {self.title}>'
