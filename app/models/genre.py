from app import db
from .base_model import BaseModel

class Genre(BaseModel):
    __tablename__ = 'genres'
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(10), nullable=True)
    
    # Relations
    artists = db.relationship('Artist', back_populates='genre', lazy='dynamic')
    tracks = db.relationship('Track', back_populates='genre', lazy='dynamic')
    fans = db.relationship('User', secondary='user_favorite_genres', back_populates='favorite_genres')
