# app/models/user.py

from app import db
from .base_model import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash

class User(BaseModel):
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    
    # Relations Many-to-Many (tables de liaison)
    favorite_artists = db.relationship('Artist', secondary='user_favorite_artists', back_populates='fans')
    favorite_genres = db.relationship('Genre', secondary='user_favorite_genres', back_populates='fans')
    favorite_tracks = db.relationship('Track', secondary='user_favorite_tracks', back_populates='fans')
    
    # Relations One-to-Many
    digs = db.relationship('Dig', back_populates='user', lazy='dynamic')
    upvotes = db.relationship('Upvote', back_populates='user', lazy='dynamic')
    redigs = db.relationship('Redig', back_populates='user', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='user', lazy='dynamic')
    
    # Follow
    following = db.relationship('Follow', foreign_keys='Follow.follower_id', back_populates='follower', lazy='dynamic')
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id', back_populates='followed', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Override de to_dict pour ajouter les compteurs"""
        base = super().to_dict()
        base.update({
            'digs_count': self.digs.count(),
            'followers_count': self.followers.count(),
            'following_count': self.following.count()
        })
        # On cache le mot de passe
        if 'password_hash' in base:
            del base['password_hash']
        return base
    
    def __repr__(self):
        return f'<User {self.username}>'
