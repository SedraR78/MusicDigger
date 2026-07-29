# app/models/associations.py
"""Tables de liaison Many-to-Many (favoris de l'utilisateur).

Une colonne ne peut pas contenir une liste : pour qu'un user ait plusieurs
artistes favoris ET qu'un artiste ait plusieurs fans, il faut une table
intermédiaire qui ne stocke que des paires.
"""

from app import db

# primary_key=True sur les deux colonnes = clé primaire composite.
# Ça empêche d'ajouter deux fois le même favori, garanti par la base.
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
