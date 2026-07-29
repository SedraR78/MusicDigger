# app/models/dig.py
from app import db
from .base_model import BaseModel


class Dig(BaseModel):
    """Un DIG = une chanson + l'avis obligatoire de l'utilisateur.

    Deux sources possibles pour le morceau :
      - track_id → un Track du catalogue (cas normal, Spotify ou YouTube)
      - les champs song_* → saisie manuelle (3e niveau de fallback)
    C'est ce qui garantit qu'un DIG peut TOUJOURS être créé.
    """

    __tablename__ = 'digs'

    # nullable=False : c'est LA règle produit centrale de MusicDigger.
    # On ne partage pas un lien nu, on dit pourquoi le son compte.
    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    track_id = db.Column(db.String(36), db.ForeignKey('tracks.id'), nullable=True)

    # Fallback manuel — utilisé seulement si track_id est NULL
    song_title = db.Column(db.String(200), nullable=True)
    song_artist = db.Column(db.String(200), nullable=True)
    song_album = db.Column(db.String(200), nullable=True)
    song_genre = db.Column(db.String(100), nullable=True)
    song_url = db.Column(db.String(300), nullable=True)
    embed_url = db.Column(db.String(300), nullable=True)

    # Compteurs dénormalisés : Trending trie par score sur toute la table.
    # Sans eux, il faudrait recompter les upvotes de chaque dig à chaque
    # affichage. Coût : risque de désync, limité par toggle() (seul point
    # du code autorisé à créer un upvote/redig).
    upvotes_count = db.Column(db.Integer, default=0, nullable=False)
    redigs_count = db.Column(db.Integer, default=0, nullable=False)
    comments_count = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('User', back_populates='digs')
    track = db.relationship('Track', back_populates='digs')

    # cascade : si on supprime un Dig, ses upvotes/redigs/comments n'ont plus
    # de sens, ils pointeraient vers du vide. On les supprime avec.
    upvotes = db.relationship('Upvote', back_populates='dig', lazy='dynamic',
                              cascade='all, delete-orphan')
    redigs = db.relationship('Redig', back_populates='dig', lazy='dynamic',
                             cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='dig', lazy='dynamic',
                               cascade='all, delete-orphan')

    # ============ Propriétés d'affichage ============
    # Elles masquent le double système : le template écrit dig.display_title
    # sans savoir si l'info vient du catalogue ou d'une saisie manuelle.

    @property
    def display_title(self):
        return self.track.title if self.track else self.song_title

    @property
    def display_artist(self):
        if self.track and self.track.artist:
            return self.track.artist.name
        return self.song_artist

    @property
    def display_album(self):
        if self.track and self.track.album:
            return self.track.album.title
        return self.song_album

    @property
    def display_genre(self):
        if self.track and self.track.genre:
            return self.track.genre.name
        return self.song_genre

    @property
    def display_cover(self):
        return self.track.cover_url if self.track else None

    @property
    def display_embed(self):
        return self.track.embed_url if self.track else self.embed_url

    # ============ Méthodes métier ============

    def score(self):
        """Score du Trending : un redig vaut 2 upvotes.

        Justification : reposter un son dans son propre feed engage bien plus
        que cliquer une flèche. Le classement récompense la diffusion.
        """
        return self.upvotes_count + (self.redigs_count * 2)

    def is_owned_by(self, user_id):
        """Vérification de propriété, utilisée par PUT et DELETE."""
        return self.user_id == user_id

    def share_url(self):
        return f'/digs/{self.id}'

    # ============ Sérialisation ============

    def to_dict(self, current_user_id=None):
        """current_user_id : la réponse dépend de QUI regarde.

        Le même DIG doit afficher le bouton upvote actif pour quelqu'un qui
        l'a déjà upvoté, et inactif pour les autres. C'est de l'état
        contextuel, il ne peut pas être stocké sur le dig.
        """
        base = super().to_dict()
        base.update({
            'title': self.display_title,
            'artist': self.display_artist,
            'album': self.display_album,
            'genre': self.display_genre,
            'cover': self.display_cover,
            'embed': self.display_embed,
            'score': self.score(),
            'share_url': self.share_url(),
            'user': {
                'id': self.user.id,
                'username': self.user.display_name,
                'avatar': self.user.avatar,
            } if self.user else None,
        })

        if current_user_id:
            base['is_upvoted'] = self.upvotes.filter_by(
                user_id=current_user_id).first() is not None
            base['is_rediged'] = self.redigs.filter_by(
                user_id=current_user_id).first() is not None
        else:
            base['is_upvoted'] = False
            base['is_rediged'] = False

        return base

    def __repr__(self):
        return f'<Dig {self.display_title}>'
