from flask import Blueprint, jsonify

discover_bp = Blueprint('discover', __name__)

@discover_bp.route('/', methods=['GET'])
def test():
    return jsonify({'message': 'Discover routes working!'}), 200
