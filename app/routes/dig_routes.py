from flask import Blueprint, jsonify

dig_bp = Blueprint('digs', __name__)

@dig_bp.route('/', methods=['GET'])
def test():
    return jsonify({'message': 'Dig routes working!'}), 200
