from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity
)
from app import db
from app.models import User, Artist, Genre, Track
from app.models.associations import user_favorite_genres

auth_bp = Blueprint('auth', __name__)

# ============================================================
# 1. REGISTER
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration"""
    data = request.get_json()
    
    # Check required fields
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields: username, email, password'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Create user
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    # Optional fields
    if data.get('bio'):
        user.bio = data['bio']
    if data.get('avatar'):
        user.avatar = data['avatar']
    
    db.session.add(user)
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'Registration successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 201


# ============================================================
# 2. LOGIN
# ============================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


# ============================================================
# 3. GET CURRENT USER
# ============================================================

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user info"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


# ============================================================
# 4. REFRESH TOKEN
# ============================================================

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token}), 200


# ============================================================
# 5. UPDATE PROFILE
# ============================================================

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if data.get('username'):
        # Check if username is taken
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Username already taken'}), 400
        user.username = data['username']
    
    if data.get('bio') is not None:
        user.bio = data['bio']
    
    if data.get('avatar'):
        user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    }), 200


# ============================================================
# 6. ONBOARDING (Save favorite artists, genres, tracks)
# ============================================================

@auth_bp.route('/onboarding', methods=['POST'])
@jwt_required()
def onboarding():
    """Save user preferences (artists, genres, tracks)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Add favorite artists
    if data.get('artist_ids'):
        artists = Artist.query.filter(Artist.id.in_(data['artist_ids'])).all()
        user.favorite_artists.extend(artists)
    
    # Add favorite genres
    if data.get('genre_ids'):
        genres = Genre.query.filter(Genre.id.in_(data['genre_ids'])).all()
        user.favorite_genres.extend(genres)
    
    # Add favorite tracks
    if data.get('track_ids'):
        tracks = Track.query.filter(Track.id.in_(data['track_ids'])).all()
        user.favorite_tracks.extend(tracks)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Onboarding completed successfully',
        'user': user.to_dict()
    }), 200


# ============================================================
# 7. SUGGEST ARTISTS (for onboarding)
# ============================================================

@auth_bp.route('/suggest/artists', methods=['GET'])
@jwt_required()
def suggest_artists():
    """Suggest artists based on search query (for onboarding)"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify({'artists': []}), 200
    
    artists = Artist.query.filter(
        Artist.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify({
        'artists': [artist.to_dict() for artist in artists]
    }), 200


# ============================================================
# 8. SUGGEST TRACKS (for onboarding)
# ============================================================

@auth_bp.route('/suggest/tracks', methods=['GET'])
@jwt_required()
def suggest_tracks():
    """Suggest tracks based on search query (for onboarding)"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify({'tracks': []}), 200
    
    tracks = Track.query.filter(
        Track.title.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify({
        'tracks': [track.to_dict() for track in tracks]
    }), 200


# ============================================================
# 9. RECOMMEND USERS TO FOLLOW (for onboarding)
# ============================================================

@auth_bp.route('/suggest/users', methods=['GET'])
@jwt_required()
def suggest_users():
    """Recommend users to follow based on preferences"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's favorite genres
    genre_ids = [g.id for g in user.favorite_genres]
    
    if genre_ids:
        # Find users with same genres (excluding self)
        suggested = User.query.join(
            user_favorite_genres, 
            User.id == user_favorite_genres.c.user_id
        ).filter(
            user_favorite_genres.c.genre_id.in_(genre_ids),
            User.id != user.id
        ).distinct().limit(10).all()
    else:
        # Fallback: random users (excluding self)
        suggested = User.query.filter(User.id != user.id).limit(10).all()
    
    return jsonify({
        'users': [user.to_dict() for user in suggested]
    }), 200
