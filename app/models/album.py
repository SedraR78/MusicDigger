from app import db
from .base_model import BaseModel

class Album(BaseModel):
    __tablename__ = 'albums'
    
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.String(36), db.ForeignKey('artists.id'), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    
    # Relations
    artist = db.relationship('Artist', back_populates='albums')
    tracks = db.relationship('Track', back_populates='album', lazy='dynamic')
