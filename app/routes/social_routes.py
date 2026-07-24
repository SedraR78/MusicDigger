from flask import Blueprint, jsonify

social_bp = Blueprint('social', __name__)

@social_bp.route('/', methods=['GET'])
def test():
    return jsonify({'message': 'Social routes working!'}), 200
