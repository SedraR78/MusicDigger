"""Routes de pages : renvoient du HTML via Jinja2, pas du JSON.

Différence avec les routes /api : celles-ci appellent DIRECTEMENT les services
et passent les objets au template. Aucun appel HTTP à notre propre API — ce
serait un aller-retour réseau inutile.

Les routes /api restent utiles pour les actions dynamiques du JS (upvote,
création de dig, suggestions) et pour tester le back indépendamment du front.
"""

from flask import Blueprint, render_template, abort

from app import db
from app.models import Dig, User
from app.services.dig_service import DigService
from app.services.genre_mapper import FEATURED_GENRES, CANONICAL_GENRES

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
@pages_bp.route('/trending')
def trending():
    """La page publique. Accessible sans compte (user story Must Have)."""
    digs = DigService.trending(period='all', limit=20)
    return render_template('trending.html',
                           digs=digs,
                           active='trending',
                           genres=FEATURED_GENRES)


@pages_bp.route('/digs/<dig_id>')
def dig_detail(dig_id):
    """Page d'un DIG : c'est l'URL de partage."""
    dig = db.session.get(Dig, dig_id)
    if dig is None:
        abort(404)
    return render_template('dig_detail.html', dig=dig, active='')


@pages_bp.route('/u/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    digs = user.digs.order_by(Dig.created_at.desc()).limit(20).all()
    return render_template('profile.html', profile_user=user, digs=digs, active='')


@pages_bp.route('/login')
def login():
    return render_template('auth/login.html', active='')


@pages_bp.route('/register')
def register():
    return render_template('auth/register.html', active='')


@pages_bp.route('/digscover')
def digscover():
    """Page DigsCover. Publique : un visiteur peut explorer par critères.

    Le contenu est chargé en fetch après l'affichage, parce qu'il dépend de
    l'état de connexion — que Jinja2 ne connaît pas (le token est côté
    navigateur, dans localStorage).
    """
    return render_template('digscover.html',
                           active='digscover',
                           featured_genres=FEATURED_GENRES,
                           all_genres=CANONICAL_GENRES)
@pages_bp.route('/feed')
def feed():
    """Le feed des personnes suivies. Le contenu est chargé en fetch parce
    qu'il dépend du token, que Jinja2 ne connaît pas."""
    return render_template('feed.html', active='feed')


@pages_bp.route('/messages')
def messages():
    return render_template('messages.html', active='messages')


@pages_bp.route('/people')
def people():
    """Annuaire simple : tous les utilisateurs actifs."""
    users = User.query.filter(User.is_deleted.is_(False)).limit(50).all()
    return render_template('people.html', users=users, active='people')
