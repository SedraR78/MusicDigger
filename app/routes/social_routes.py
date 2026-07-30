"""Profils publics et système de follow."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app import db
from app.models import User, Dig, Follow

social_bp = Blueprint('social', __name__)


def error(message, code):
    return jsonify({'error': message, 'code': code}), code


def optional_user_id():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None


def find_user(username):
    return User.query.filter_by(username=username).first()


# ============================================================
# PROFIL PUBLIC
# ============================================================

@social_bp.route('/<username>', methods=['GET'])
def get_profile(username):
    """GET /api/users/<username> — public.

    to_dict() retire déjà l'email et le password_hash : la même méthode sert
    aux profils publics, donc le défaut doit être restrictif.
    """
    user = find_user(username)
    if user is None:
        return error('User not found', 404)

    viewer_id = optional_user_id()

    payload = user.to_dict()
    payload['digs'] = [
        d.to_dict(current_user_id=viewer_id)
        for d in user.digs.order_by(Dig.created_at.desc()).limit(20).all()
    ]

    # Le bouton Follow doit-il afficher "Follow" ou "Following" ?
    if viewer_id and viewer_id != user.id:
        payload['is_following'] = Follow.query.filter_by(
            follower_id=viewer_id, followed_id=user.id).first() is not None
    else:
        payload['is_following'] = False

    payload['is_self'] = viewer_id == user.id
    return jsonify({'user': payload}), 200


# ============================================================
# FOLLOW / UNFOLLOW
# ============================================================

@social_bp.route('/<username>/follow', methods=['POST'])
@jwt_required()
def toggle_follow(username):
    """POST /api/users/<username>/follow — bascule le suivi.

    Un seul endpoint pour suivre et arrêter de suivre : le front envoie
    l'intention et reçoit le nouvel état.
    """
    target = find_user(username)
    if target is None or target.is_deleted:
        return error('User not found', 404)

    try:
        following = Follow.toggle(get_jwt_identity(), target.id)
    except ValueError as exc:
        return error(str(exc), 400)   # tentative de se suivre soi-même

    return jsonify({
        'is_following': following,
        'followers_count': target.followers.count(),
    }), 200


# ============================================================
# LISTES
# ============================================================

@social_bp.route('/<username>/followers', methods=['GET'])
def followers(username):
    user = find_user(username)
    if user is None:
        return error('User not found', 404)

    return jsonify({
        'users': [f.follower.to_dict() for f in user.followers.all()
                  if f.follower],
    }), 200


@social_bp.route('/<username>/following', methods=['GET'])
def following(username):
    user = find_user(username)
    if user is None:
        return error('User not found', 404)

    return jsonify({
        'users': [f.followed.to_dict() for f in user.following.all()
                  if f.followed],
    }), 200
