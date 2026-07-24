from app import db
from .base_model import BaseModel

class Upvote(BaseModel):
    __tablename__ = 'upvotes'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'dig_id', name='unique_user_upvote'),)
    
    user = db.relationship('User', back_populates='upvotes')
    dig = db.relationship('Dig', back_populates='upvotes')
