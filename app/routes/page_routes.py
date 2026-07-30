"""Routes de pages : renvoient du HTML via Jinja2, pas du JSON.

Différence avec les routes /api : celles-ci appellent DIRECTEMENT les services
et passent les objets au template. Aucun appel HTTP à notre propre API — ce
serait un aller-retour réseau inutile.

Les routes /api restent utiles pour les actions dynamiques du JS (upvote,
création de dig, suggestions) et pour tester le back indépendamment du front.
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, abort, request

from app import db
from app.models import Dig, User, Artist, Track , Genre
from app.services.dig_service import DigService
from app.services.genre_mapper import FEATURED_GENRES, CANONICAL_GENRES

pages_bp = Blueprint('pages', __name__)

PER_PAGE = 20

@pages_bp.route('/')
@pages_bp.route('/trending')
def trending():
    """La page publique. Accessible sans compte (user story Must Have).

    Quatre tris : day / week / all classent par score, latest par date.
    Un filtre par genre peut se combiner avec n'importe quel tri.
    """
    period = request.args.get('period', 'all')
    if period not in ('day', 'week', 'all', 'latest'):
        period = 'all'

    genre_name = request.args.get('genre')
    page = request.args.get('page', 1, type=int)

    query = Dig.query

    # Le filtre par genre passe par le Track : un DIG hérite du genre
    # du morceau dont il parle.
    if genre_name:
        genre = Genre.query.filter(Genre.name.ilike(genre_name)).first()
        if genre:
            query = (query.join(Track, Dig.track_id == Track.id)
                          .filter(Track.genre_id == genre.id))
        else:
            genre_name = None   # genre inconnu : on ignore le filtre

    if period == 'day':
        query = query.filter(Dig.created_at >= datetime.utcnow() - timedelta(days=1))
    elif period == 'week':
        query = query.filter(Dig.created_at >= datetime.utcnow() - timedelta(weeks=1))

    if period == 'latest':
        query = query.order_by(Dig.created_at.desc())
    else:
        # Le calcul du score se fait EN SQL grâce aux compteurs dénormalisés
        score = Dig.upvotes_count + (Dig.redigs_count * 2)
        query = query.order_by(score.desc(), Dig.created_at.desc())

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    # On ne propose que les genres qui ont RÉELLEMENT des digs :
    # afficher un filtre qui renvoie zéro résultat est une mauvaise idée.
    active_genres = (db.session.query(Genre.name)
                     .join(Track, Track.genre_id == Genre.id)
                     .join(Dig, Dig.track_id == Track.id)
                     .distinct()
                     .order_by(Genre.name)
                     .all())

    return render_template('trending.html',
                           digs=pagination.items,
                           pagination=pagination,
                           period=period,
                           genre=genre_name,
                           genres=[g[0] for g in active_genres],
                           active='trending')


@pages_bp.route('/feed')
def feed():
    """Le feed des personnes suivies.

    Le contenu est chargé en fetch parce qu'il dépend du token, que Jinja2
    ne connaît pas — il est dans localStorage, côté navigateur.
    """
    return render_template('feed.html', active='feed')


@pages_bp.route('/digscover')
def digscover():
    """Page DigsCover. Publique : un visiteur peut explorer par critères.

    Comme pour le feed, le contenu est chargé en fetch : il dépend de
    l'état de connexion.
    """
    return render_template('digscover.html',
                           active='digscover',
                           featured_genres=FEATURED_GENRES,
                           all_genres=CANONICAL_GENRES)


@pages_bp.route('/messages')
def messages():
    return render_template('messages.html', active='messages')


@pages_bp.route('/people')
def people():
    """Annuaire des utilisateurs actifs, paginé."""
    page = request.args.get('page', 1, type=int)

    pagination = (User.query
                  .filter(User.is_deleted.is_(False))
                  .order_by(User.created_at.desc())
                  .paginate(page=page, per_page=24, error_out=False))

    return render_template('people.html',
                           users=pagination.items,
                           pagination=pagination,
                           active='people')




@pages_bp.route('/digs/<dig_id>')
def dig_detail(dig_id):
    """Page d'un DIG : c'est l'URL de partage."""
    dig = db.session.get(Dig, dig_id)
    if dig is None:
        abort(404)
    return render_template('dig_detail.html', dig=dig, active='')


@pages_bp.route('/u/<username>')
def profile(username):
    """Profil public, avec ses DIGs paginés."""
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)

    page = request.args.get('page', 1, type=int)

    pagination = (user.digs
                  .order_by(Dig.created_at.desc())
                  .paginate(page=page, per_page=PER_PAGE, error_out=False))

    return render_template('profile.html',
                           profile_user=user,
                           digs=pagination.items,
                           pagination=pagination,
                           active='')


@pages_bp.route('/artist/<path:name>')
def artist_page(name):
    """Tous les DIGs postés sur les morceaux d'un artiste.

    Différent de DigsCover : ici on montre ce que la communauté a DIT sur cet
    artiste, pas des morceaux à découvrir.
    """
    artist = Artist.query.filter(Artist.name.ilike(name)).first()
    if artist is None:
        abort(404)

    page = request.args.get('page', 1, type=int)

    pagination = (Dig.query
                  .join(Track, Dig.track_id == Track.id)
                  .filter(Track.artist_id == artist.id)
                  .order_by(Dig.created_at.desc())
                  .paginate(page=page, per_page=PER_PAGE, error_out=False))

    return render_template('artist.html',
                           artist=artist,
                           digs=pagination.items,
                           pagination=pagination,
                           active='')


@pages_bp.route('/login')
def login():
    return render_template('auth/login.html', active='')


@pages_bp.route('/register')
def register():
    return render_template('auth/register.html', active='')

@pages_bp.route('/about')
def about():
    """Page manifeste. Explique le produit à quelqu'un qui arrive sans contexte."""
    stats = {
        'digs':    Dig.query.count(),
        'tracks':  Track.query.count(),
        'diggers': User.query.filter(User.is_deleted.is_(False)).count(),
    }
    return render_template('about.html', stats=stats, active='about')
