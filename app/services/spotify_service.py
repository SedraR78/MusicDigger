"""Accès au catalogue Spotify. Source primaire des métadonnées.

Rôle clé : NORMALISER. Le reste de l'application ne voit jamais le format brut
de Spotify — c'est ce qui rend Spotify et YouTube interchangeables pour
DigService.

Authentification : Client Credentials. L'application s'authentifie avec ses
propres clés, aucun utilisateur ne se connecte à Spotify. On n'accède qu'au
catalogue public.

⚠️ Note : l'API ne renvoie plus les genres sur l'objet artiste. Le genre est
donc résolu ailleurs (voir artist_genres.py).
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import current_app


class SpotifyService:

    _client = None   # singleton : chaque instanciation négocie un token

    @classmethod
    def get_client(cls):
        if cls._client is None:
            client_id = current_app.config.get('SPOTIFY_CLIENT_ID')
            client_secret = current_app.config.get('SPOTIFY_CLIENT_SECRET')

            if not client_id or not client_secret:
                current_app.logger.warning('Spotify credentials missing')
                return None

            cls._client = spotipy.Spotify(
                client_credentials_manager=SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret,
                )
            )
        return cls._client

    @classmethod
    def search(cls, query, limit=10):
        """Cherche des morceaux. Retourne une liste normalisée, ou [].

        Ne lève JAMAIS d'exception : si Spotify est indisponible, on renvoie
        une liste vide et l'appelant bascule sur YouTube.
        """
        try:
            client = cls.get_client()
            if client is None:
                return []

            results = client.search(q=query, type='track', limit=limit)
            items = results.get('tracks', {}).get('items', [])
            return [cls._normalize(item) for item in items]
        except Exception as exc:
            current_app.logger.warning(f'Spotify search failed: {exc}')
            return []

    @classmethod
    def get_track(cls, spotify_id):
        """Récupère un morceau par son identifiant.

        Utilisée à la création d'un DIG : le client n'envoie qu'un id, le
        serveur va chercher les métadonnées lui-même.
        """
        try:
            client = cls.get_client()
            if client is None:
                return None
            return cls._normalize(client.track(spotify_id))
        except Exception as exc:
            current_app.logger.warning(f'Spotify get_track failed: {exc}')
            return None

    @staticmethod
    def _normalize(item):
        """Traduit une réponse Spotify vers NOTRE format interne.

        Les .get() partout : les APIs externes renvoient parfois des champs
        manquants. item['album']['images'][0] planterait.
        """
        album = item.get('album') or {}
        images = album.get('images') or []
        artists = item.get('artists') or [{}]
        track_id = item.get('id')

        return {
            'source': 'spotify',
            'external_id': track_id,
            'title': item.get('name'),
            'artist_name': artists[0].get('name'),
            'artist_external_id': artists[0].get('id'),
            'album_title': album.get('name'),
            'album_external_id': album.get('id'),
            'album_year': (album.get('release_date') or '')[:4] or None,
            'cover_url': images[0]['url'] if images else None,
            'preview_url': item.get('preview_url'),
            'embed_url': f'https://open.spotify.com/embed/track/{track_id}',
            'duration_ms': item.get('duration_ms'),
            'popularity': item.get('popularity'),
        }
