from app import db
from .base_model import BaseModel
class Track(BaseModel):
    __tablename__ = 'tracks'
    
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.String(36), db.ForeignKey('artists.id'), nullable=False)
    album_id = db.Column(db.String(36), db.ForeignKey('albums.id'), nullable=True)
    genre_id = db.Column(db.String(36), db.ForeignKey('genres.id'), nullable=True)
    spotify_id = db.Column(db.String(100), nullable=True, unique=True)
    youtube_id = db.Column(db.String(100), nullable=True, unique=True)
    cover_url = db.Column(db.String(200), nullable=True)
    preview_url = db.Column(db.String(200), nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    popularity = db.Column(db.Integer, nullable=True)
    
    # Relations
    artist = db.relationship('Artist', back_populates='tracks')
    album = db.relationship('Album', back_populates='tracks')
    genre = db.relationship('Genre', back_populates='tracks')
    fans = db.relationship('User', secondary='user_favorite_tracks', back_populates='favorite_tracks')
    digs = db.relationship('Dig', back_populates='track')  # ← Les DIGs associés
    
    @property
    def digs_count(self):
        return self.digs.count() if self.digs else 0
    
    @property
    def upvotes_count(self):
        return sum(dig.upvotes_count for dig in self.digs) if self.digs else 0
    
    @property
    def redigs_count(self):
        return sum(dig.redigs_count for dig in self.digs) if self.digs else 0
    
    def to_dict(self):
        base = super().to_dict()
        base.update({
            'artist': self.artist.to_dict() if self.artist else None,
            'album': self.album.to_dict() if self.album else None,
            'genre': self.genre.to_dict() if self.genre else None,
            'digs_count': self.digs_count,
            'upvotes_count': self.upvotes_count,
            'redigs_count': self.redigs_count,
            'has_digs': self.digs_count > 0
        })
        return base
