from flask import request, jsonify
from app import app
from app.config import Config
from functools import wraps

def require_api_key(function):
    """Honor the explicit key toggle without enabling enhanced queue semantics."""
    @wraps(function)
    def guarded(*args, **kwargs):
        if Config.REQUIRE_API_KEY:
            key = request.headers.get('X-API-Key')
            if not key or key not in Config.API_KEYS:
                return jsonify({'error': 'Unauthorized', 'message': 'Valid API key required'}), 401
        return function(*args, **kwargs)
    return guarded


queue = []
queue_position = {}

@app.route('/queue', methods=['POST'])
@require_api_key
def join_queue():
    data = request.json
    name = data['name']
    if name not in queue_position:
        queue.append(name)
        queue_position[name] = len(queue)
    return jsonify({'position': queue_position[name]})

@app.route('/queue/<name>', methods=['GET'])
@require_api_key
def check_position(name):
    if name in queue_position:
        return jsonify({'position': queue_position[name]})
    else:
        return jsonify({'position': -1})

@app.route('/queue/next', methods=['POST'])
@require_api_key
def next_in_queue():
    if queue:
        name = queue.pop(0)
        queue_position.pop(name, None)
        for i, remaining_name in enumerate(queue):
            queue_position[remaining_name] = i + 1
        return jsonify({'next': name})
    else:
        return jsonify({'next': None})
