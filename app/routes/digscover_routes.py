"""Routes DigsCover : recommandations de MORCEAUX (pas de DIGs).

Le même endpoint sert deux publics :
    - visiteur  → résultats basés uniquement sur les critères saisis
    - connecté  → recommandations personnalisées (profil de goûts +
                  filtrage collaboratif), avec exclusion de l'historique

Rappel du choix produit : on recommande des tracks du catalogue et pas des
posts existants, sinon on ne pourrait faire découvrir que des sons déjà
postés — et personne ne pourrait jamais être le premier à diguer un morceau.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app import db
from app.models import User
from app.services.digscover_service import DigsCoverService
from app.services.genre_mapper import FEATURED_GENRES, CANONICAL_GENRES

digscover_bp = Blueprint('digscover', __name__)


def error(message, code):
    return jsonify({'error': message, 'code': code}), code


def optional_user():
    """L'utilisateur connecté, ou None si la requête est anonyme."""
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if not user_id:
            return None
        user = db.session.get(User, user_id)
        return None if (user is None or user.is_deleted) else user
    except Exception:
        return None


def serialize(results):
    """Transforme [(track, label)] en JSON.

    Le label explique POURQUOI le morceau est proposé ("Because you dig
    Digga D", "Fans also dig this"). La recommandation est explicable,
    pas une boîte noire — c'est l'inverse du problème que le produit dénonce.
    """
    payload = []
    for track, label in results:
        item = track.to_dict()
        item['reason_label'] = label
        payload.append(item)
    return payload


# ============================================================
# DIGSCOVER
# ============================================================

@digscover_bp.route('', methods=['GET'])
@digscover_bp.route('/', methods=['GET'])
def digscover():
    """GET /api/digscover?artists=&songs=&genres=

    Auth optionnelle. Trois cas :
        1. connecté sans critères  → recommandations personnalisées
        2. critères fournis         → recherche par critères
        3. anonyme sans critères    → état vide + invitation à choisir

    Le cas 3 est volontaire : DigsCover sans critères et sans compte n'a
    aucun signal, donc rien de pertinent à proposer.
    """
    artists = request.args.get('artists')
    songs = request.args.get('songs')
    genres = request.args.get('genres')
    has_criteria = any([artists, songs, genres])

    user = optional_user()

    # 1. Connecté, pas de critères → personnalisé
    if user is not None and not has_criteria:
        results = DigsCoverService.for_user(user, limit=20)
        return jsonify({
            'tracks': serialize(results),
            'mode': 'personalized',
            'featured_genres': FEATURED_GENRES,
        }), 200

    # 2. Des critères → recherche par critères (connecté ou non)
    if has_criteria:
        results = DigsCoverService.by_criteria(
            artists=artists, songs=songs, genres=genres, limit=20)
        return jsonify({
            'tracks': serialize(results),
            'mode': 'criteria',
            'featured_genres': FEATURED_GENRES,
        }), 200

    # 3. Anonyme sans critères → état vide
    return jsonify({
        'tracks': [],
        'mode': 'empty',
        'prompt': 'Tell us what you like to start digging',
        'featured_genres': FEATURED_GENRES,
        'all_genres': CANONICAL_GENRES,
    }), 200


# ============================================================
# RANDOM DIG
# ============================================================

@digscover_bp.route('/random', methods=['GET'])
def random_dig():
    """GET /api/digscover/random — un DIG au hasard, hors personnalisation.

    Public : c'est le bouton qui permet de sortir de sa bulle sans compte.
    """
    dig = DigsCoverService.random_dig()
    if dig is None:
        return error('No dig available yet', 404)

    user = optional_user()
    return jsonify({
        'dig': dig.to_dict(current_user_id=user.id if user else None),
    }), 200
