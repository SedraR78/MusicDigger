from app import db
from .base_model import BaseModel

class Comment(BaseModel):
    __tablename__ = 'comments'
    
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)
    
    user = db.relationship('User', back_populates='comments')
    dig = db.relationship('Dig', back_populates='comments')
