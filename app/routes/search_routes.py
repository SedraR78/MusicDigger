"""Recherche globale : utilisateurs, artistes, albums, morceaux, genres.

Différence avec /api/digs/search : celle-ci cherche dans NOTRE base (ce qui
existe déjà sur la plateforme), alors que /api/digs/search interroge Spotify
et YouTube pour trouver un son à poster.
"""

from flask import Blueprint, request, jsonify

from app.models import User, Artist, Album, Track, Dig

search_bp = Blueprint('search', __name__)

VALID_TYPES = ('all', 'user', 'artist', 'album', 'track', 'genre')
LIMIT = 8


def error(message, code):
    return jsonify({'error': message, 'code': code}), code


@search_bp.route('', methods=['GET'])
@search_bp.route('/', methods=['GET'])
def search():
    """GET /api/search?q=...&type=all|user|artist|album|track|genre

    Public : un visiteur doit pouvoir explorer avant de créer un compte.
    """
    query = request.args.get('q', '').strip()
    kind = request.args.get('type', 'all')

    if kind not in VALID_TYPES:
        return error(f'type must be one of: {", ".join(VALID_TYPES)}', 400)

    if len(query) < 2:
        return jsonify({'results': {}, 'query': query}), 200

    pattern = f'%{query}%'
    results = {}

    if kind in ('all', 'user'):
        users = (User.query
                 .filter(User.username.ilike(pattern),
                         User.is_deleted.is_(False))   # les comptes retirés sont invisibles
                 .limit(LIMIT).all())
        results['users'] = [u.to_dict() for u in users]

    if kind in ('all', 'artist'):
        artists = Artist.query.filter(Artist.name.ilike(pattern)).limit(LIMIT).all()
        results['artists'] = [{
            'id': a.id,
            'name': a.name,
            'genre': a.genre.name if a.genre else None,
            'tracks_count': a.tracks.count(),
        } for a in artists]

    if kind in ('all', 'album'):
        albums = Album.query.filter(Album.title.ilike(pattern)).limit(LIMIT).all()
        results['albums'] = [{
            'id': al.id,
            'title': al.title,
            'artist': al.artist.name if al.artist else None,
            'year': al.year,
        } for al in albums]

    if kind in ('all', 'track'):
        tracks = Track.query.filter(Track.title.ilike(pattern)).limit(LIMIT).all()
        results['tracks'] = [t.to_dict() for t in tracks]

    if kind in ('all', 'genre'):
        # On cherche les morceaux d'un genre plutôt que le genre lui-même :
        # ce qui intéresse l'utilisateur, c'est la musique, pas l'étiquette.
        tracks = (Track.query
                  .join(Track.genre)
                  .filter(Track.genre.has())
                  .limit(LIMIT * 2).all())
        matching = [t for t in tracks
                    if t.genre and query.lower() in t.genre.name.lower()]
        results['by_genre'] = [t.to_dict() for t in matching[:LIMIT]]

    return jsonify({'results': results, 'query': query}), 200


@search_bp.route('/suggest', methods=['GET'])
def suggest():
    """GET /api/search/suggest?q=... — suggestions légères pour la dropdown.

    Version allégée : uniquement les libellés, pas les objets complets. C'est
    appelé à chaque frappe de l'utilisateur, donc la réponse doit être minimale.
    """
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'suggestions': []}), 200

    pattern = f'%{query}%'
    suggestions = []

    for u in User.query.filter(User.username.ilike(pattern),
                               User.is_deleted.is_(False)).limit(4).all():
        suggestions.append({'type': 'user', 'label': u.username, 'id': u.id})

    for a in Artist.query.filter(Artist.name.ilike(pattern)).limit(4).all():
        suggestions.append({'type': 'artist', 'label': a.name, 'id': a.id})

    for t in Track.query.filter(Track.title.ilike(pattern)).limit(4).all():
        label = f'{t.title} — {t.artist.name}' if t.artist else t.title
        suggestions.append({'type': 'track', 'label': label, 'id': t.id})

    return jsonify({'suggestions': suggestions}), 200
