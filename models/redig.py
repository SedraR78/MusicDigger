from app import db
from .base_model import BaseModel

class Redig(BaseModel):
    __tablename__ = 'redigs'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    dig_id = db.Column(db.String(36), db.ForeignKey('digs.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'dig_id', name='unique_user_redig'),)
    
    user = db.relationship('User', back_populates='redigs')
    dig = db.relationship('Dig', back_populates='redigs')
