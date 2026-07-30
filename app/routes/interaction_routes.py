"""Upvotes, redigs et commentaires.

Les toggle() des models font le travail : ils créent ou suppriment
l'interaction ET maintiennent le compteur dénormalisé du Dig, dans la même
transaction. C'est ce qui garantit que les compteurs restent justes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Dig, Upvote, Redig, Comment

interaction_bp = Blueprint('interactions', __name__)


def error(message, code):
    return jsonify({'error': message, 'code': code}), code


def get_dig_or_404(dig_id):
    return db.session.get(Dig, dig_id)


# ============================================================
# UPVOTE
# ============================================================

@interaction_bp.route('/<dig_id>/upvote', methods=['POST'])
@jwt_required()
def toggle_upvote(dig_id):
    """POST /api/digs/<id>/upvote — bascule l'upvote.

    Un seul endpoint pour ajouter ET retirer : le front n'a pas à savoir
    dans quel état il est, il envoie l'intention et reçoit le nouvel état.
    La contrainte UNIQUE(user_id, dig_id) garantit l'unicité même en cas de
    double-clic (race condition).
    """
    dig = get_dig_or_404(dig_id)
    if dig is None:
        return error('Dig not found', 404)

    active, count = Upvote.toggle(get_jwt_identity(), dig)
    return jsonify({'is_upvoted': active, 'upvotes_count': count}), 200


# ============================================================
# REDIG
# ============================================================

@interaction_bp.route('/<dig_id>/redig', methods=['POST'])
@jwt_required()
def toggle_redig(dig_id):
    """POST /api/digs/<id>/redig — bascule le redig.

    Un redig pèse 2× un upvote dans le score Trending : reposter un son dans
    son propre feed engage bien plus que cliquer une flèche.
    """
    dig = get_dig_or_404(dig_id)
    if dig is None:
        return error('Dig not found', 404)

    user_id = get_jwt_identity()

    # On ne redig pas son propre dig : il est déjà dans son feed
    if dig.user_id == user_id:
        return error('You cannot redig your own dig', 400)

    active, count = Redig.toggle(user_id, dig)
    return jsonify({'is_rediged': active, 'redigs_count': count}), 200


# ============================================================
# COMMENTAIRES
# ============================================================

@interaction_bp.route('/<dig_id>/comments', methods=['GET'])
def list_comments(dig_id):
    """GET /api/digs/<id>/comments — public, du plus ancien au plus récent."""
    dig = get_dig_or_404(dig_id)
    if dig is None:
        return error('Dig not found', 404)

    comments = dig.comments.order_by(Comment.created_at.asc()).all()
    return jsonify({'comments': [c.to_dict() for c in comments]}), 200


@interaction_bp.route('/<dig_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(dig_id):
    """POST /api/digs/<id>/comments

    Pas de contrainte d'unicité : un utilisateur peut commenter plusieurs fois
    le même DIG. C'est une conversation, pas un vote.
    """
    dig = get_dig_or_404(dig_id)
    if dig is None:
        return error('Dig not found', 404)

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return error('Comment content is required', 400)

    comment = Comment(content=content, user_id=get_jwt_identity(), dig_id=dig.id)
    db.session.add(comment)

    # Le compteur dénormalisé est incrémenté dans la MÊME transaction que
    # l'insertion : soit les deux passent, soit aucun.
    dig.comments_count += 1
    db.session.commit()

    return jsonify({
        'comment': comment.to_dict(),
        'comments_count': dig.comments_count,
    }), 201


@interaction_bp.route('/comments/<comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return error('Comment not found', 404)

    if not comment.is_owned_by(get_jwt_identity()):
        return error('You can only delete your own comments', 403)

    dig = comment.dig
    db.session.delete(comment)
    if dig:
        dig.comments_count = max(0, dig.comments_count - 1)
    db.session.commit()

    # ← LA modification : on renvoie le nouveau compteur au front
    return jsonify({
        'message': 'Comment deleted',
        'comments_count': dig.comments_count if dig else 0,
    }), 200
