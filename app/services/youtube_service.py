"""Source de repli quand Spotify ne trouve rien.

Même interface et même format de sortie que SpotifyService : c'est ce qui les
rend interchangeables. Le code appelant ne fait pas la différence.

Pourquoi YouTube en second : Spotify a des métadonnées plus propres (album,
durée, popularité) mais un catalogue incomplet — remixes, freestyles, lives,
mixtapes. C'est une grande partie de ce qui circule dans le rap UK.
"""

import requests
from flask import current_app

SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'


class YouTubeService:

    @classmethod
    def search(cls, query, limit=10):
        api_key = current_app.config.get('YOUTUBE_API_KEY')
        if not api_key:
            current_app.logger.warning('YouTube API key missing')
            return []

        try:
            response = requests.get(SEARCH_URL, params={
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'videoCategoryId': '10',   # 10 = catégorie Musique
                'maxResults': limit,
                'key': api_key,
            }, timeout=5)   # sans timeout, une API muette gèle le serveur
            response.raise_for_status()
            items = response.json().get('items', [])
            return [cls._normalize(item) for item in items]
        except Exception as exc:
            current_app.logger.warning(f'YouTube search failed: {exc}')
            return []

    @classmethod
    def get_video(cls, video_id):
        api_key = current_app.config.get('YOUTUBE_API_KEY')
        if not api_key:
            return None

        try:
            response = requests.get(VIDEOS_URL, params={
                'part': 'snippet',
                'id': video_id,
                'key': api_key,
            }, timeout=5)
            response.raise_for_status()
            items = response.json().get('items', [])
            if not items:
                return None

            item = items[0]
            # videos renvoie l'id à plat, search le renvoie imbriqué.
            # On aligne pour réutiliser _normalize.
            item['id'] = {'videoId': video_id}
            return cls._normalize(item)
        except Exception as exc:
            current_app.logger.warning(f'YouTube get_video failed: {exc}')
            return None

    @staticmethod
    def _normalize(item):
        """Format IDENTIQUE à SpotifyService._normalize.

        Les champs absents chez YouTube restent présents avec None : c'est ce
        qui garantit que DigService traite les deux sources de la même façon.
        """
        video_id = item.get('id', {}).get('videoId')
        snippet = item.get('snippet', {})
        thumbnails = snippet.get('thumbnails', {})

        return {
            'source': 'youtube',
            'external_id': video_id,
            'title': snippet.get('title'),
            'artist_name': snippet.get('channelTitle'),
            'artist_external_id': None,
            'album_title': None,          # notion inexistante chez YouTube
            'album_external_id': None,
            'album_year': (snippet.get('publishedAt') or '')[:4] or None,
            'cover_url': (thumbnails.get('high') or {}).get('url'),
            'preview_url': None,
            'embed_url': f'https://www.youtube.com/embed/{video_id}',
            'duration_ms': None,
            'popularity': None,
        }
