# app/models/__init__.py
"""Point d'entrée des models : un seul import charge toutes les tables.

Critique pour Flask-Migrate : il ne détecte que les models importés.
Un model absent de ce fichier = une table absente de ta base.
"""

# 1. Les tables de liaison d'abord (elles ne dépendent de rien)
from .associations import (
    user_favorite_artists,
    user_favorite_genres,
    user_favorite_tracks,
)

# 2. La classe mère
from .base_model import BaseModel

# 3. Le catalogue musical
from .genre import Genre
from .artist import Artist
from .album import Album
from .track import Track

# 4. Les utilisateurs et le social
from .user import User
from .dig import Dig
from .upvote import Upvote
from .redig import Redig
from .comment import Comment
from .follow import Follow
from .user_history import UserHistory

from .conversation import Conversation
from .message import Message

__all__ = [
    'BaseModel',
    'Genre', 'Artist', 'Album', 'Track',
    'User', 'Dig', 'Upvote', 'Redig', 'Comment', 'Follow', 'UserHistory',
    'user_favorite_artists', 'user_favorite_genres', 'user_favorite_tracks',
    'Conversation', 'Message',
]
