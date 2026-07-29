"""Blueprint d'authentification.

Endpoints (Stage 3, section 5) :
    POST   /api/auth/register     {username, email, password} → {user, access_token}
    POST   /api/auth/login        {email, password}           → {user, tokens}
    POST   /api/auth/refresh                                  → {access_token}
    GET    /api/auth/me                                       → {user}
    POST   /api/auth/onboarding   {artist_ids[], genre_ids[], track_ids[]}
    DELETE /api/auth/account      {password}                  → {message}
"""

import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from app import db, limiter
from app.models import User, Artist, Genre, Track, user_favorite_genres

auth_bp = Blueprint('auth', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MIN_PASSWORD_LENGTH = 8


def error(message, code):
    """Format d'erreur unique pour toute l'API (Stage 3)."""
    return jsonify({'error': message, 'code': code}), code


def current_user():
    """L'utilisateur du token. None si le compte a été retiré entre-temps."""
    user = db.session.get(User, get_jwt_identity())
    return None if (user is None or user.is_deleted) else user


# ============================================================
# 1. REGISTER
# ============================================================

@auth_bp.route('/register', methods=['POST'])
@limiter.limit('10 per hour')
def register():
    data = request.get_json(silent=True) or {}

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    # --- Validation ---
    if not username or not email or not password:
        return error('username, email and password are required', 400)

    if not EMAIL_RE.match(email):
        return error('Invalid email format', 400)

    if len(password) < MIN_PASSWORD_LENGTH:
        return error(f'Password must be at least {MIN_PASSWORD_LENGTH} characters', 400)

    if len(username) < 3 or len(username) > 80:
        return error('Username must be between 3 and 80 characters', 400)

    # 409 Conflict : la ressource existe déjà (Stage 3, table des codes)
    if User.query.filter_by(email=email).first():
        return error('Email already registered', 409)

    if User.query.filter_by(username=username).first():
        return error('Username already taken', 409)

    # --- Création ---
    user = User(username=username, email=email)
    user.set_password(password)          # hachage scrypt + sel
    user.save()

    return jsonify({
        'user': user.to_dict(),
        'access_token': create_access_token(identity=user.id),
        'refresh_token': create_refresh_token(identity=user.id),
    }), 201


# ============================================================
# 2. LOGIN
# ============================================================

@auth_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')   # protection contre le bruteforce
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return error('email and password are required', 400)

    user = User.query.filter_by(email=email).first()

    # Message volontairement identique dans les deux cas : on ne révèle pas
    # si l'email existe en base (sinon on offre un énumérateur de comptes).
    if user is None or not user.check_password(password):
        return error('Invalid email or password', 401)

    if user.is_deleted:
        return error('This account has been deleted', 401)

    return jsonify({
        'user': user.to_dict(),
        'access_token': create_access_token(identity=user.id),
        'refresh_token': create_refresh_token(identity=user.id),
    }), 200


# ============================================================
# 3. REFRESH
# ============================================================

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)     # exige le refresh token, pas l'access token
def refresh():
    """Un access token vit 1h. Le refresh token (30j) permet d'en obtenir
    un nouveau sans redemander le mot de passe."""
    user = current_user()
    if user is None:
        return error('User not found', 404)

    return jsonify({'access_token': create_access_token(identity=user.id)}), 200


# ============================================================
# 4. ME
# ============================================================

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = current_user()
    if user is None:
        return error('User not found', 404)

    # Vue privée : ici on a le droit de renvoyer l'email et les préférences
    payload = user.to_dict()
    payload.update({
        'email': user.email,
        'favorite_artists': [{'id': a.id, 'name': a.name} for a in user.favorite_artists],
        'favorite_genres': [{'id': g.id, 'name': g.name} for g in user.favorite_genres],
        'favorite_tracks': [{'id': t.id, 'title': t.title} for t in user.favorite_tracks],
        'onboarding_complete': bool(user.favorite_artists and user.favorite_genres),
    })
    return jsonify(payload), 200


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    user = current_user()
    if user is None:
        return error('User not found', 404)

    data = request.get_json(silent=True) or {}

    if 'username' in data:
        username = (data['username'] or '').strip()
        if len(username) < 3:
            return error('Username must be at least 3 characters', 400)
        taken = User.query.filter_by(username=username).first()
        if taken and taken.id != user.id:
            return error('Username already taken', 409)
        user.username = username

    if 'bio' in data:
        user.bio = data['bio']
    if 'avatar' in data:
        user.avatar = data['avatar']

    user.save()
    return jsonify({'user': user.to_dict()}), 200


# ============================================================
# 5. ONBOARDING
# ============================================================

@auth_bp.route('/onboarding', methods=['POST'])
@jwt_required()
def onboarding():
    """Minimums imposés par le Stage 1 : 3 artistes, 2 genres, 1 titre.

    Ces seuils ne sont pas décoratifs : sans eux, DigsCover n'a aucun signal
    de goût et ne peut rien recommander de pertinent au premier usage.
    """
    user = current_user()
    if user is None:
        return error('User not found', 404)

    data = request.get_json(silent=True) or {}
    artist_ids = data.get('artist_ids') or []
    genre_ids = data.get('genre_ids') or []
    track_ids = data.get('track_ids') or []

    if len(artist_ids) < 3:
        return error('At least 3 favorite artists are required', 400)
    if len(genre_ids) < 2:
        return error('At least 2 favorite genres are required', 400)
    if len(track_ids) < 1:
        return error('At least 1 favorite track is required', 400)

    artists = Artist.query.filter(Artist.id.in_(artist_ids)).all()
    genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
    tracks = Track.query.filter(Track.id.in_(track_ids)).all()

    # Un id envoyé mais inexistant en base = requête invalide, on le signale
    if len(artists) != len(set(artist_ids)):
        return error('Some artist ids do not exist', 400)
    if len(genres) != len(set(genre_ids)):
        return error('Some genre ids do not exist', 400)
    if len(tracks) != len(set(track_ids)):
        return error('Some track ids do not exist', 400)

    # On remplace au lieu d'ajouter : l'onboarding peut être rejoué
    user.favorite_artists = artists
    user.favorite_genres = genres
    user.favorite_tracks = tracks
    user.save()

    return jsonify({
        'user': user.to_dict(),
        'suggested_users': _suggest_users(user),
    }), 200


def _suggest_users(user, limit=10):
    """Comptes à suivre : ceux qui partagent au moins un genre favori."""
    genre_ids = [g.id for g in user.favorite_genres]

    query = User.query.filter(User.id != user.id, User.is_deleted.is_(False))

    if genre_ids:
        query = (query
                 .join(user_favorite_genres, User.id == user_favorite_genres.c.user_id)
                 .filter(user_favorite_genres.c.genre_id.in_(genre_ids))
                 .distinct())

    return [u.to_dict() for u in query.limit(limit).all()]


# ============================================================
# 6. DELETE ACCOUNT
# ============================================================

@auth_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Anonymise le compte (« RetiredDigger ») au lieu de le supprimer.

    Le mot de passe est redemandé : un token volé ne doit pas suffire à
    détruire un compte. C'est une opération irréversible.
    """
    user = current_user()
    if user is None:
        return error('User not found', 404)

    data = request.get_json(silent=True) or {}
    password = data.get('password') or ''

    if not password:
        return error('Password confirmation is required', 400)

    if not user.check_password(password):
        return error('Invalid password', 403)

    user.retire()
    return jsonify({'message': 'Account retired'}), 200
