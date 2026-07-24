from flask import Blueprint, jsonify

search_bp = Blueprint('search', __name__)

@search_bp.route('/', methods=['GET'])
def test():
    return jsonify({'message': 'Search routes working!'}), 200
