from app import db
from .base_model import BaseModel

class UserHistory(BaseModel):
    __tablename__ = 'user_histories'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=db.func.now())
    
    __table_args__ = (db.UniqueConstraint('user_id', 'dig_id', name='unique_user_dig_history'),)
    
    user = db.relationship('User', back_populates='history')
    dig = db.relationship('Dig')
