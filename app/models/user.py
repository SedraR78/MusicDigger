# app/models/user.py
from app import db
from .base_model import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
import uuid


class User(BaseModel):
    __tablename__ = 'users'

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # 256 et pas 128 : les hash scrypt de Werkzeug dépassent 128 caractères.
    # Colonne trop courte = hash tronqué = l'utilisateur ne peut plus se log.
    password_hash = db.Column(db.String(256), nullable=False)

    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(300), nullable=True)

    # Compte "retiré" : anonymisé mais la ligne existe encore, pour ne pas
    # trouer les conversations et commentaires des autres utilisateurs.
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # ---------- Many-to-Many (favoris) ----------
    favorite_artists = db.relationship('Artist', secondary='user_favorite_artists',
                                       back_populates='fans')
    favorite_genres = db.relationship('Genre', secondary='user_favorite_genres',
                                      back_populates='fans')
    favorite_tracks = db.relationship('Track', secondary='user_favorite_tracks',
                                      back_populates='fans')

    # ---------- One-to-Many ----------
    digs = db.relationship('Dig', back_populates='user', lazy='dynamic')
    upvotes = db.relationship('Upvote', back_populates='user', lazy='dynamic')
    redigs = db.relationship('Redig', back_populates='user', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='user', lazy='dynamic')
    history = db.relationship('UserHistory', back_populates='user', lazy='dynamic')
    sent_messages = db.relationship('Message', back_populates='sender', lazy='dynamic')

    # ---------- Follow : deux relations vers la MÊME table ----------
    # follows a deux FK vers users (follower_id et followed_id). SQLAlchemy
    # ne peut pas deviner laquelle sert à quoi → on précise foreign_keys.
    # Sans ça : AmbiguousForeignKeysError au démarrage.
    following = db.relationship('Follow', foreign_keys='Follow.follower_id',
                                back_populates='follower', lazy='dynamic')
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id',
                                back_populates='followed', lazy='dynamic')

    # ==================== Mot de passe ====================

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Ne déchiffre pas : recalcule le hash et compare."""
        return check_password_hash(self.password_hash, password)

    # ==================== Suppression de compte ====================

    def retire(self):
        """Anonymise le compte en "RetiredDigger" au lieu de le supprimer.

        Données perso effacées + login impossible = droit à l'effacement.
        Digs/comments/messages conservés = les fils des autres restent entiers.
        Comportement (upvotes, redigs, follows, historique) réellement supprimé.
        """
        # 1. Données personnelles effacées.
        #    username reste unique en base (contrainte), donc on met une valeur
        #    aléatoire et on AFFICHE "RetiredDigger" via display_name.
        self.username = f'retired_{uuid.uuid4().hex[:8]}'
        self.email = f'retired_{uuid.uuid4().hex[:8]}@deleted.local'
        self.password_hash = generate_password_hash(uuid.uuid4().hex)
        self.bio = None
        self.avatar = None
        self.is_deleted = True

        # 2. Traces de comportement supprimées
        self.upvotes.delete()
        self.redigs.delete()
        self.history.delete()
        self.following.delete()
        self.followers.delete()

        # 3. Préférences vidées
        self.favorite_artists.clear()
        self.favorite_genres.clear()
        self.favorite_tracks.clear()

        db.session.commit()
        return self

    @property
    def display_name(self):
        return 'RetiredDigger' if self.is_deleted else self.username

    # ==================== DigsCover ====================

    def taste_profile(self):
        """Profil de goûts explicite, consommé par DigsCoverService."""
        return {
            'artist_ids': [a.id for a in self.favorite_artists],
            'genre_ids': [g.id for g in self.favorite_genres],
            'track_ids': [t.id for t in self.favorite_tracks],
        }

    # ==================== Sérialisation ====================

    def to_dict(self):
        base = super().to_dict()
        base.pop('password_hash', None)   # jamais exposé
        base.pop('email', None)           # privé : to_dict sert aussi aux profils publics
        base.update({
            'username': self.display_name,
            'digs_count': self.digs.count(),
            'followers_count': self.followers.count(),
            'following_count': self.following.count(),
        })
        return base

    def __repr__(self):
        return f'<User {self.username}>'
