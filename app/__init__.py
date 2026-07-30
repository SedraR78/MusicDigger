# app/__init__.py
from datetime import timedelta
import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

# Extensions créées "à vide" au niveau du module, branchées sur l'app
# dans create_app(). C'est ce qui évite les imports circulaires entre
# les models (qui importent db) et l'application.
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)   # limite par adresse IP


def create_app():
    app = Flask(__name__)

    # ---------- Configuration ----------
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///musicdigger.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
    app.config['SPOTIFY_CLIENT_ID'] = os.getenv('SPOTIFY_CLIENT_ID')
    app.config['SPOTIFY_CLIENT_SECRET'] = os.getenv('SPOTIFY_CLIENT_SECRET')
    app.config['YOUTUBE_API_KEY'] = os.getenv('YOUTUBE_API_KEY')

    # Access token court : un JWT ne peut pas être révoqué, donc on réduit
    # la fenêtre d'exploitation d'un token volé. Le refresh token (long)
    # évite à l'utilisateur de se reconnecter toutes les heures.
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # ---------- Extensions ----------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)

    # Indispensable : Flask-Migrate ne détecte que les models importés.
    from app import models  # noqa: F401

    # ---------- Routes de santé ----------
    @app.route('/')
    def home():
        return jsonify({'message': 'MusicDigger is running!'}), 200

    # ---------- Blueprints ----------
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # À décommenter au fur et à mesure que les fichiers sont prêts :
    from app.routes.dig_routes import dig_bp
    from app.routes.interaction_routes import interaction_bp
    from app.routes.social_routes import social_bp
    # from app.routes.digscover_routes import digscover_bp
    from app.routes.message_routes import message_bp
    # from app.routes.search_routes import search_bp
    #
    app.register_blueprint(dig_bp, url_prefix='/api/digs')
    app.register_blueprint(interaction_bp, url_prefix='/api/digs')
    app.register_blueprint(social_bp, url_prefix='/api/users')
    # app.register_blueprint(digscover_bp, url_prefix='/api/digscover')
    app.register_blueprint(message_bp, url_prefix='/api')
    # app.register_blueprint(search_bp, url_prefix='/api/search')

    # ---------- Gestion des erreurs ----------
    # Sans ces handlers, une erreur renvoie une page HTML de Flask, ce qui
    # casse un front qui attend du JSON. Format unique défini au Stage 3.

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'code': 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed', 'code': 405}), 405

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({'error': 'Too many attempts, try again later', 'code': 429}), 429

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()   # une transaction cassée ne doit pas rester ouverte
        return jsonify({'error': 'Internal server error', 'code': 500}), 500

    # ---------- Réponses JWT en JSON ----------
    # Par défaut Flask-JWT-Extended renvoie ses propres messages. On les
    # aligne sur notre format d'erreur.

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({'error': 'Authorization token is missing', 'code': 401}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({'error': 'Invalid token', 'code': 401}), 401

    @jwt.expired_token_loader
    def expired_token(header, payload):
        return jsonify({'error': 'Token has expired', 'code': 401}), 401

    return app
