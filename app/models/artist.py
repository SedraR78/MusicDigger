
# app/models/artist.py
from app import db
from .base_model import BaseModel

class Artist(BaseModel):
    __tablename__ = 'artists'
    
    name = db.Column(db.String(200), unique=True, nullable=False)
    genre_id = db.Column(db.String(36), db.ForeignKey('genres.id'), nullable=True)
    
    # Relations
    genre = db.relationship('Genre', back_populates='artists')
    tracks = db.relationship('Track', back_populates='artist', lazy='dynamic')
    albums = db.relationship('Album', back_populates='artist', lazy='dynamic')
    fans = db.relationship('User', secondary='user_favorite_artists', back_populates='favorite_artists')
