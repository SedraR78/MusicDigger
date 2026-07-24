from flask import Blueprint, jsonify

interaction_bp = Blueprint('interactions', __name__)

@interaction_bp.route('/', methods=['GET'])
def test():
    return jsonify({'message': 'Interaction routes working!'}), 200
