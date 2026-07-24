from app import db
from .base_model import BaseModel

class Follow(BaseModel):
    __tablename__ = 'follows'
    
    follower_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),)
    
    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following')
    followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers')
