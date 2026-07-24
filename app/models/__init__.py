from app import db

# Import BaseModel first (others inherit from it)
from .base_model import BaseModel

# Import all models
from .user import User
from .artist import Artist
from .track import Track
from .album import Album
from .genre import Genre
from .dig import Dig
from .upvote import Upvote
from .redig import Redig
from .comment import Comment
from .follow import Follow
from .user_history import UserHistory

# Many-to-Many relationship tables (must be defined here)
user_favorite_artists = db.Table(
    'user_favorite_artists',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('artist_id', db.String(36), db.ForeignKey('artists.id'), primary_key=True)
)

user_favorite_genres = db.Table(
    'user_favorite_genres',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('genre_id', db.String(36), db.ForeignKey('genres.id'), primary_key=True)
)

user_favorite_tracks = db.Table(
    'user_favorite_tracks',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('track_id', db.String(36), db.ForeignKey('tracks.id'), primary_key=True)
)

__all__ = [
    'BaseModel',
    'User',
    'Artist',
    'Track',
    'Album',
    'Genre',
    'Dig',
    'Upvote',
    'Redig',
    'Comment',
    'Follow',
    'UserHistory',
    'user_favorite_artists',
    'user_favorite_genres',
    'user_favorite_tracks'
]
