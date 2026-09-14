from flask import request, jsonify
from app import app

queue = []
queue_position = {}

@app.route('/queue', methods=['POST'])
def join_queue():
    data = request.json
    name = data['name']
    if name not in queue_position:
        queue.append(name)
        queue_position[name] = len(queue)
    return jsonify({'position': queue_position[name]})

@app.route('/queue/<name>', methods=['GET'])
def check_position(name):
    if name in queue_position:
        return jsonify({'position': queue_position[name]})
    else:
        return jsonify({'position': -1})

@app.route('/queue/next', methods=['POST'])
def next_in_queue():
    if queue:
        name = queue.pop(0)
        queue_position.pop(name, None)
        for i, remaining_name in enumerate(queue):
            queue_position[remaining_name] = i + 1
        return jsonify({'next': name})
    else:
        return jsonify({'next': None})
