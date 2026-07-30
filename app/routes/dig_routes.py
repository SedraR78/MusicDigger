"""Routes des DIGs : recherche, création, lecture, trending, feed.

Les controllers restent minces : recevoir, valider, déléguer au service,
répondre. Toute la logique métier est dans DigService.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app import db
from app.models import Dig
from app.services.dig_service import DigService
from app.services.genre_mapper import CANONICAL_GENRES, FEATURED_GENRES

dig_bp = Blueprint('digs', __name__)


def error(message, code):
    return jsonify({'error': message, 'code': code}), code


def optional_user_id():
    """L'id du user connecté, ou None. Sert aux routes publiques qui
    personnalisent leur réponse quand un token est présent (is_upvoted…)."""
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None


# ============================================================
# RECHERCHE DE MORCEAUX (alimente le modal de création)
# ============================================================

@dig_bp.route('/search', methods=['GET'])
@jwt_required()
def search_tracks():
    """GET /api/digs/search?q=...

    Chaque résultat porte un champ 'source' (spotify | youtube) que le front
    affiche en badge. C'est ce qui rend le fallback visible pour l'utilisateur.
    """
    query = request.args.get('q', '')
    if len(query.strip()) < 2:
        return jsonify({'results': []}), 200

    results = DigService.search_tracks(query, limit=8)
    return jsonify({
        'results': results,
        'source': results[0]['source'] if results else None,
        'genres': FEATURED_GENRES,      # pour le sélecteur de genre du modal
    }), 200


# ============================================================
# TRENDING (public)
# ============================================================

@dig_bp.route('/trending', methods=['GET'])
def trending():
    """GET /api/digs/trending?period=day|week|all

    Public : accessible sans compte (user story Must Have n°3).
    """
    period = request.args.get('period', 'all')
    if period not in ('day', 'week', 'all'):
        return error('period must be day, week or all', 400)

    user_id = optional_user_id()
    digs = DigService.trending(period=period, limit=20)

    return jsonify({
        'digs': [d.to_dict(current_user_id=user_id) for d in digs],
        'period': period,
    }), 200


# ============================================================
# FEED (privé)
# ============================================================

@dig_bp.route('/feed', methods=['GET'])
@jwt_required()
def feed():
    """GET /api/digs/feed?page=1 — les DIGs des personnes suivies."""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)

    digs = DigService.feed(user_id, page=page, per_page=20)
    return jsonify({
        'digs': [d.to_dict(current_user_id=user_id) for d in digs],
        'page': page,
    }), 200


# ============================================================
# CRÉER UN DIG
# ============================================================

@dig_bp.route('', methods=['POST'])
@dig_bp.route('/', methods=['POST'])
@jwt_required()
def create_dig():
    """POST /api/digs

    Deux formes acceptées :
        {source, external_id, content, genre?}  → depuis le catalogue
        {manual: {title, artist, ...}, content} → saisie manuelle

    Le client n'envoie qu'un identifiant, jamais les métadonnées : c'est le
    serveur qui interroge l'API et remplit titre, artiste, pochette. Un
    utilisateur ne peut donc pas falsifier les informations d'un son.
    """
    data = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()

    content = data.get('content')
    genre = data.get('genre')

    if genre and genre not in CANONICAL_GENRES:
        return error('Unknown genre', 400)

    try:
        dig = DigService.create_dig(
            user_id=user_id,
            content=content,
            source=data.get('source'),
            external_id=data.get('external_id'),
            genre=genre,
            manual=data.get('manual'),
        )
    except ValueError as exc:
        return error(str(exc), 400)

    return jsonify({'dig': dig.to_dict(current_user_id=user_id)}), 201


# ============================================================
# LIRE / MODIFIER / SUPPRIMER UN DIG
# ============================================================

@dig_bp.route('/<dig_id>', methods=['GET'])
def get_dig(dig_id):
    """GET /api/digs/<id> — public : c'est l'URL de partage."""
    dig = db.session.get(Dig, dig_id)
    if dig is None:
        return error('Dig not found', 404)

    return jsonify({'dig': dig.to_dict(current_user_id=optional_user_id())}), 200


@dig_bp.route('/<dig_id>', methods=['PUT'])
@jwt_required()
def update_dig(dig_id):
    """PUT /api/digs/<id> — on ne modifie que son avis, pas le morceau."""
    user_id = get_jwt_identity()
    dig = db.session.get(Dig, dig_id)
    if dig is None:
        return error('Dig not found', 404)

    # 403 et pas 404 : on sait qui tu es, tu n'as juste pas le droit
    if not dig.is_owned_by(user_id):
        return error('You can only edit your own digs', 403)

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return error('An opinion is required', 400)

    dig.content = content
    dig.save()
    return jsonify({'dig': dig.to_dict(current_user_id=user_id)}), 200


@dig_bp.route('/<dig_id>', methods=['DELETE'])
@jwt_required()
def delete_dig(dig_id):
    """DELETE /api/digs/<id>

    Le cascade delete-orphan supprime automatiquement les upvotes, redigs
    et commentaires du dig — ils n'auraient plus de sens sans lui.
    """
    user_id = get_jwt_identity()
    dig = db.session.get(Dig, dig_id)
    if dig is None:
        return error('Dig not found', 404)

    if not dig.is_owned_by(user_id):
        return error('You can only delete your own digs', 403)

    dig.delete()
    return jsonify({'message': 'Dig deleted'}), 200
