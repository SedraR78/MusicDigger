# app/models/dig.py

from app import db
from .base_model import BaseModel

class Dig(BaseModel):
    __tablename__ = 'digs'
    
    content = db.Column(db.Text, nullable=False)
    
    # Soit on a un track_id (recherche)...
    track_id = db.Column(db.String(36), db.ForeignKey('tracks.id'), nullable=True)
    track = db.relationship('Track', back_populates='digs')  # ← Relation vers Track
    
    # ... soit on a des champs fallback
    song_title = db.Column(db.String(200), nullable=True)
    song_artist = db.Column(db.String(200), nullable=True)
    song_album = db.Column(db.String(200), nullable=True)
    song_genre = db.Column(db.String(100), nullable=True)
    song_url = db.Column(db.String(200), nullable=True)
    embed_url = db.Column(db.String(200), nullable=True)
    
    # Compteurs
    upvotes_count = db.Column(db.Integer, default=0)
    redigs_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    
    # Foreign Key
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='digs')
    
    # Relations
    upvotes = db.relationship('Upvote', back_populates='dig', lazy='dynamic')
    redigs = db.relationship('Redig', back_populates='dig', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='dig', lazy='dynamic')
    history_entries = db.relationship('UserHistory', back_populates='dig', lazy='dynamic')
    
    @property
    def display_title(self):
        if self.track:
            return self.track.title
        return self.song_title
    
    @property
    def display_artist(self):
        if self.track:
            return self.track.artist.name
        return self.song_artist
        
    @property
    def display_album(self):
        """Retourne l'album à afficher"""
        if self.track and self.track.album:
            return self.track.album.title
        return self.song_album
    
    @property
    def display_genre(self):
        """Retourne le genre à afficher"""
        if self.track and self.track.genre:
            return self.track.genre.name
        return self.song_genre
    
    @property
    def display_cover(self):
        """Retourne la pochette d'album"""
        if self.track and self.track.cover_url:
            return self.track.cover_url
        return None
    
    def to_dict(self):
        base = super().to_dict()
        base.update({
            'title': self.display_title,
            'artist': self.display_artist,
            'album': self.display_album,
            'genre': self.display_genre,
            'cover': self.display_cover,
            'score': self.score(),
            'user': self.user.to_dict() if self.user else None,
            'is_upvoted': False,
            'is_rediged': False,
            'track': self.track.to_dict() if self.track else None
        })
        return base
    
    def __repr__(self):
        return f'<Dig {self.display_title} - {self.display_artist}>'
