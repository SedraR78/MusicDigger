"""Orchestrateur de la création et de la lecture des DIGs.

Implémente le sequence diagram n°1 du Stage 3 :
    cache local → Spotify → YouTube → mise en cache → création du DIG
"""

import re
from datetime import datetime, timedelta

from app import db
from app.models import Dig, Track, Artist, Album, Genre, Follow
from app.services.spotify_service import SpotifyService
from app.services.youtube_service import YouTubeService
from app.services.artist_genres import lookup_genre

# Les caractères spéciaux cassent la recherche Spotify : "Pink + White" ne
# renvoie rien. On les remplace par des espaces.
SPECIAL_CHARS = re.compile(r'[+&|!(){}\[\]^"~*?:\\/]')


class DigService:

    # ==================== Recherche ====================

    @staticmethod
    def clean_query(query):
        return SPECIAL_CHARS.sub(' ', query or '').strip()

    @staticmethod
    def search_tracks(query, limit=10):
        """Recherche avec repli : Spotify d'abord, YouTube ensuite.

        Si Spotify renvoie une liste vide — morceau absent OU API en panne —
        on bascule sur YouTube. Chaque résultat porte un champ 'source' que le
        front utilise pour afficher un badge.
        """
        cleaned = DigService.clean_query(query)
        if not cleaned:
            return []

        results = SpotifyService.search(cleaned, limit)
        if results:
            return results

        return YouTubeService.search(cleaned, limit)

    # ==================== Genres ====================

    @staticmethod
    def _get_or_create_genre(name):
        if not name:
            return None
        genre = Genre.query.filter_by(name=name).first()
        if genre is None:
            genre = Genre(name=name)
            db.session.add(genre)
            db.session.flush()
        return genre

    @staticmethod
    def _resolve_genre_name(artist_name, user_genre=None):
        """Cascade de résolution du genre.

        1. mapping local par artiste (le plus fiable)
        2. genre proposé par l'utilisateur au moment du dig
        3. None → DigsCover utilise ses autres signaux
        """
        return lookup_genre(artist_name) or user_genre

    # ==================== Mise en cache ====================

    @staticmethod
    def _get_or_create_artist(payload, genre=None):
        name = payload.get('artist_name')
        if not name:
            return None

        external_id = payload.get('artist_external_id')

        # On cherche par identifiant externe (fiable), puis par nom
        artist = None
        if external_id:
            artist = Artist.query.filter_by(spotify_id=external_id).first()
        if artist is None:
            artist = Artist.query.filter_by(name=name).first()

        if artist is not None:
            # Artiste connu mais pas encore classé : on le renseigne
            if artist.genre_id is None and genre is not None:
                artist.genre_id = genre.id
            return artist

        artist = Artist(
            name=name,
            spotify_id=external_id,
            genre_id=genre.id if genre else None,
        )
        db.session.add(artist)
        db.session.flush()   # obtient l'id sans valider la transaction
        return artist

    @staticmethod
    def _get_or_create_album(payload, artist):
        title = payload.get('album_title')
        if not title or artist is None:
            return None

        external_id = payload.get('album_external_id')

        album = None
        if external_id:
            album = Album.query.filter_by(spotify_id=external_id).first()
        if album is None:
            album = Album.query.filter_by(title=title, artist_id=artist.id).first()
        if album is not None:
            return album

        year = payload.get('album_year')
        album = Album(
            title=title,
            artist_id=artist.id,
            spotify_id=external_id,
            year=int(year) if year and str(year).isdigit() else None,
        )
        db.session.add(album)
        db.session.flush()
        return album

    @staticmethod
    def get_or_create_track(payload, user_genre=None):
        """Met un morceau en cache local, avec son artiste, album et genre.

        Le cache évite de rappeler l'API pour un morceau déjà connu, économise
        du quota, et garde l'app fonctionnelle si l'API externe tombe.
        """
        source = payload.get('source', 'spotify')
        field = 'spotify_id' if source == 'spotify' else 'youtube_id'
        external_id = payload.get('external_id')

        if not external_id:
            return None

        genre_name = DigService._resolve_genre_name(
            payload.get('artist_name'), user_genre)

        existing = Track.query.filter_by(**{field: external_id}).first()
        if existing:
            # Morceau connu mais non classé : le premier genre proposé le
            # renseigne pour tout le monde.
            if existing.genre_id is None and genre_name:
                genre = DigService._get_or_create_genre(genre_name)
                if genre:
                    existing.genre_id = genre.id
                    if existing.artist and existing.artist.genre_id is None:
                        existing.artist.genre_id = genre.id
                    db.session.commit()
            return existing

        genre = DigService._get_or_create_genre(genre_name) if genre_name else None
        artist = DigService._get_or_create_artist(payload, genre=genre)
        album = DigService._get_or_create_album(payload, artist)

        track = Track(
            title=payload.get('title'),
            artist_id=artist.id if artist else None,
            album_id=album.id if album else None,
            genre_id=genre.id if genre else None,
            cover_url=payload.get('cover_url'),
            preview_url=payload.get('preview_url'),
            embed_url=payload.get('embed_url'),
            duration_ms=payload.get('duration_ms'),
            popularity=payload.get('popularity'),
            **{field: external_id}
        )
        db.session.add(track)
        db.session.commit()
        return track

    # ==================== Résolution par identifiant ====================

    @staticmethod
    def resolve_track(source, external_id, user_genre=None):
        """Récupère un morceau depuis son identifiant externe.

        Le client n'envoie qu'un id — jamais les métadonnées. C'est le serveur
        qui interroge l'API et remplit le titre, l'artiste, la pochette. Un
        utilisateur ne peut donc pas falsifier les informations d'un son : la
        source de vérité reste l'API, pas le navigateur.
        """
        if source not in ('spotify', 'youtube') or not external_id:
            return None

        field = 'spotify_id' if source == 'spotify' else 'youtube_id'

        cached = Track.query.filter_by(**{field: external_id}).first()
        if cached:
            genre_name = DigService._resolve_genre_name(
                cached.artist.name if cached.artist else None, user_genre)
            if cached.genre_id is None and genre_name:
                genre = DigService._get_or_create_genre(genre_name)
                if genre:
                    cached.genre_id = genre.id
                    db.session.commit()
            return cached

        payload = (SpotifyService.get_track(external_id) if source == 'spotify'
                   else YouTubeService.get_video(external_id))
        if payload is None:
            return None

        return DigService.get_or_create_track(payload, user_genre=user_genre)

    # ==================== Création ====================

    @staticmethod
    def create_dig(user_id, content, source=None, external_id=None,
                   genre=None, manual=None):
        """Crée un DIG. L'avis est obligatoire : c'est LA règle produit.

        Deux chemins :
            - source + external_id → le serveur résout le morceau
            - manual               → saisie manuelle (3e niveau de repli)

        Un utilisateur peut poster plusieurs DIGs sur le même morceau : son
        avis peut évoluer, ou porter sur un aspect différent. C'est volontaire,
        donc pas de contrainte d'unicité sur (user_id, track_id).
        """
        if not content or not content.strip():
            raise ValueError('An opinion is required to post a DIG')

        dig = Dig(user_id=user_id, content=content.strip())

        if source and external_id:
            track = DigService.resolve_track(source, external_id, user_genre=genre)
            if track is None:
                raise ValueError('Track not found')
            dig.track_id = track.id

        elif manual:
            # Ni Spotify ni YouTube n'ont trouvé : on accepte quand même
            if not manual.get('title'):
                raise ValueError('A song title is required')
            dig.song_title = manual.get('title')
            dig.song_artist = manual.get('artist')
            dig.song_album = manual.get('album')
            dig.song_genre = manual.get('genre') or lookup_genre(manual.get('artist'))
            dig.song_url = manual.get('url')
            dig.embed_url = manual.get('embed_url')

        else:
            raise ValueError('A track or manual song details are required')

        return dig.save()

    # ==================== Lectures ====================

    @staticmethod
    def trending(period='all', limit=20):
        """Classement par score = upvotes + 2 × redigs.

        Le tri se fait EN SQL grâce aux compteurs dénormalisés : une seule
        requête, 20 lignes rapatriées.
        """
        query = Dig.query

        if period == 'day':
            query = query.filter(Dig.created_at >= datetime.utcnow() - timedelta(days=1))
        elif period == 'week':
            query = query.filter(Dig.created_at >= datetime.utcnow() - timedelta(weeks=1))

        score = Dig.upvotes_count + (Dig.redigs_count * 2)
        return query.order_by(score.desc(), Dig.created_at.desc()).limit(limit).all()

    @staticmethod
    def feed(user_id, page=1, per_page=20):
        """Les DIGs des personnes suivies, du plus récent au plus ancien."""
        followed_ids = [f.followed_id for f in
                        Follow.query.filter_by(follower_id=user_id).all()]
        if not followed_ids:
            return []

        return (Dig.query
                .filter(Dig.user_id.in_(followed_ids))
                .order_by(Dig.created_at.desc())
                .paginate(page=page, per_page=per_page, error_out=False)
                .items)
