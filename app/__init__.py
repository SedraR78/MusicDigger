from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///musicdigger.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    
    @app.route('/')
    def home():
        return jsonify({'message': 'MusicDigger is running!'}), 200
    
    @app.route('/test')
    def test():
        return jsonify({'message': 'Test route works!'}), 200
    
    # 🔥 UNIQUEMENT AUTH POUR TESTER
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # 🔥 TOUT LE RESTE COMMENTÉ
    # from app.routes.dig_routes import dig_bp
    # from app.routes.interaction_routes import interaction_bp
    # from app.routes.social_routes import social_bp
    # from app.routes.discover_routes import discover_bp
    # from app.routes.search_routes import search_bp
    
    # app.register_blueprint(dig_bp, url_prefix='/api/digs')
    # app.register_blueprint(interaction_bp, url_prefix='/api/interactions')
    # app.register_blueprint(social_bp, url_prefix='/api/social')
    # app.register_blueprint(discover_bp, url_prefix='/api/discover')
    # app.register_blueprint(search_bp, url_prefix='/api/search')
    
    return app
