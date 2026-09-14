from flask import request, jsonify
from app import app
from app.config import Config
from functools import wraps
import threading
import time
import logging
from datetime import datetime, timedelta
import sqlite3
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe lock for queue operations
queue_lock = threading.RLock()

# In-memory queue structures
queue = []
queue_position = {}
task_metadata = {}  # Store task metadata (priority, timestamp, etc.)
task_status = {}    # Track task execution status

# Metrics storage
metrics = {
    'total_tasks': 0,
    'completed_tasks': 0,
    'failed_tasks': 0,
    'current_queue_size': 0,
    'avg_wait_time': 0,
    'task_history': []
}

# Persistence layer
class PersistenceLayer:
    def __init__(self, db_path='queue_data.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize SQLite database
        
        Note: Table and column names are hardcoded constants and should never
        come from user input to prevent SQL injection vulnerabilities.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queue_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT UNIQUE NOT NULL,
                    position INTEGER,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    def save_queue_state(self, queue_data, position_data, metadata_data):
        """Save current queue state to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM queue_state')
            for task_name in queue_data:
                cursor.execute('''
                    INSERT INTO queue_state (task_name, position, priority, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (
                    task_name,
                    position_data.get(task_name, -1),
                    metadata_data.get(task_name, {}).get('priority', 0),
                    json.dumps(metadata_data.get(task_name, {}))
                ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save queue state: {e}")
            return False

    def load_queue_state(self):
        """Load queue state from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT task_name, position, priority, metadata FROM queue_state ORDER BY position')
            rows = cursor.fetchall()
            conn.close()

            loaded_queue = []
            loaded_positions = {}
            loaded_metadata = {}

            for row in rows:
                task_name, position, priority, metadata_json = row
                loaded_queue.append(task_name)
                loaded_positions[task_name] = position
                loaded_metadata[task_name] = json.loads(metadata_json) if metadata_json else {}

            return loaded_queue, loaded_positions, loaded_metadata
        except Exception as e:
            logger.error(f"Failed to load queue state: {e}")
            return [], {}, {}

    def save_metric(self, metric_type, metric_value):
        """Save a metric to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO metrics (metric_type, metric_value)
                VALUES (?, ?)
            ''', (metric_type, metric_value))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save metric: {e}")

# Initialize persistence
persistence = PersistenceLayer(Config.DATABASE_PATH)

# Load initial state
loaded_queue, loaded_positions, loaded_metadata = persistence.load_queue_state()
if loaded_queue:
    queue = loaded_queue
    queue_position = loaded_positions
    task_metadata = loaded_metadata
    logger.info(f"Loaded {len(queue)} tasks from persistent storage")

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.REQUIRE_API_KEY:
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in Config.API_KEYS:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized', 'message': 'Valid API key required'}), 401

        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def update_metrics(action, value=None):
    """Update metrics"""
    if not Config.ENABLE_METRICS:
        return

    with queue_lock:
        if action == 'task_added':
            metrics['total_tasks'] += 1
            metrics['current_queue_size'] = len(queue)
        elif action == 'task_completed':
            metrics['completed_tasks'] += 1
            metrics['current_queue_size'] = len(queue)
            if value:
                metrics['task_history'].append({
                    'task': value,
                    'completed_at': datetime.now().isoformat(),
                    'status': 'completed'
                })
        elif action == 'task_failed':
            metrics['failed_tasks'] += 1
            if value:
                metrics['task_history'].append({
                    'task': value,
                    'completed_at': datetime.now().isoformat(),
                    'status': 'failed'
                })

        # Keep only recent history
        if len(metrics['task_history']) > 100:
            metrics['task_history'] = metrics['task_history'][-100:]

        # Save to persistence
        persistence.save_metric(action, value or 0)

def reorder_queue_by_priority():
    """Reorder queue based on priority"""
    if not Config.ENABLE_PRIORITY_QUEUE:
        return

    with queue_lock:
        queue.sort(key=lambda name: (
            -task_metadata.get(name, {}).get('priority', 0),
            task_metadata.get(name, {}).get('timestamp', time.time())
        ))

        # Update positions
        for i, task_name in enumerate(queue):
            queue_position[task_name] = i + 1

# Routes
@app.route('/queue', methods=['POST'])
@require_api_key
def join_queue():
    """Add a task to the queue"""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'Task name is required'}), 400

        name = data['name']
        priority = data.get('priority', 0)

        with queue_lock:
            # Check queue size limit
            if len(queue) >= Config.MAX_QUEUE_SIZE:
                logger.warning(f"Queue full, rejecting task: {name}")
                return jsonify({'error': 'Queue Full', 'message': 'Maximum queue size reached'}), 429

            # Add to queue if not already present
            if name not in queue_position:
                queue.append(name)
                task_metadata[name] = {
                    'priority': priority,
                    'timestamp': time.time(),
                    'added_at': datetime.now().isoformat()
                }

                # Reorder by priority if enabled
                reorder_queue_by_priority()

                # Update position
                queue_position[name] = queue.index(name) + 1

                # Initialize task status
                task_status[name] = 'queued'

                # Update metrics
                update_metrics('task_added')

                # Persist state
                persistence.save_queue_state(queue, queue_position, task_metadata)

                logger.info(f"Task added: {name} at position {queue_position[name]}")

            return jsonify({
                'position': queue_position[name],
                'priority': task_metadata[name]['priority'],
                'queue_size': len(queue)
            })

    except Exception as e:
        logger.error(f"Error in join_queue: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/queue/<name>', methods=['GET'])
@require_api_key
def check_position(name):
    """Check the position of a task in the queue"""
    try:
        with queue_lock:
            if name in queue_position:
                return jsonify({
                    'position': queue_position[name],
                    'status': task_status.get(name, 'unknown'),
                    'metadata': task_metadata.get(name, {}),
                    'queue_size': len(queue)
                })
            else:
                return jsonify({
                    'position': -1,
                    'status': 'not_found',
                    'message': 'Task not in queue'
                })

    except Exception as e:
        logger.error(f"Error in check_position: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/queue/next', methods=['POST'])
@require_api_key
def next_in_queue():
    """Remove the next task from the queue"""
    try:
        with queue_lock:
            if queue:
                name = queue.pop(0)
                queue_position.pop(name, None)
                metadata = task_metadata.pop(name, {})
                task_status.pop(name, None)

                # Update remaining positions
                for i, remaining_name in enumerate(queue):
                    queue_position[remaining_name] = i + 1

                # Update metrics
                update_metrics('task_completed', name)

                # Persist state
                persistence.save_queue_state(queue, queue_position, task_metadata)

                logger.info(f"Task completed: {name}")

                return jsonify({
                    'next': name,
                    'metadata': metadata,
                    'remaining': len(queue)
                })
            else:
                return jsonify({
                    'next': None,
                    'remaining': 0
                })

    except Exception as e:
        logger.error(f"Error in next_in_queue: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/queue/remove/<name>', methods=['DELETE'])
@require_api_key
def remove_from_queue(name):
    """Remove a specific task from the queue"""
    try:
        with queue_lock:
            if name in queue_position:
                queue.remove(name)
                queue_position.pop(name, None)
                task_metadata.pop(name, None)
                task_status.pop(name, None)

                # Update positions
                for i, remaining_name in enumerate(queue):
                    queue_position[remaining_name] = i + 1

                # Update metrics
                update_metrics('task_failed', name)

                # Persist state
                persistence.save_queue_state(queue, queue_position, task_metadata)

                logger.info(f"Task removed: {name}")

                return jsonify({
                    'message': 'Task removed successfully',
                    'task': name
                })
            else:
                return jsonify({
                    'error': 'Not Found',
                    'message': 'Task not in queue'
                }), 404

    except Exception as e:
        logger.error(f"Error in remove_from_queue: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/queue/list', methods=['GET'])
@require_api_key
def list_queue():
    """List all tasks in the queue"""
    try:
        with queue_lock:
            task_list = []
            for task_name in queue:
                task_list.append({
                    'name': task_name,
                    'position': queue_position.get(task_name, -1),
                    'priority': task_metadata.get(task_name, {}).get('priority', 0),
                    'status': task_status.get(task_name, 'queued'),
                    'added_at': task_metadata.get(task_name, {}).get('added_at', 'unknown')
                })

            return jsonify({
                'queue': task_list,
                'total': len(task_list)
            })

    except Exception as e:
        logger.error(f"Error in list_queue: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/metrics', methods=['GET'])
@require_api_key
def get_metrics():
    """Get queue metrics"""
    try:
        if not Config.ENABLE_METRICS:
            return jsonify({'error': 'Metrics disabled'}), 403

        with queue_lock:
            return jsonify({
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"Error in get_metrics: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        with queue_lock:
            health_status = {
                'status': 'healthy',
                'queue_size': len(queue),
                'max_queue_size': Config.MAX_QUEUE_SIZE,
                'persistence': 'enabled',
                'timestamp': datetime.now().isoformat()
            }

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/queue/clear', methods=['POST'])
@require_api_key
def clear_queue():
    """Clear all tasks from the queue (admin operation)"""
    try:
        with queue_lock:
            count = len(queue)
            queue.clear()
            queue_position.clear()
            task_metadata.clear()
            task_status.clear()

            # Persist state
            persistence.save_queue_state(queue, queue_position, task_metadata)

            logger.warning(f"Queue cleared, removed {count} tasks")

            return jsonify({
                'message': 'Queue cleared successfully',
                'tasks_removed': count
            })

    except Exception as e:
        logger.error(f"Error in clear_queue: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500
