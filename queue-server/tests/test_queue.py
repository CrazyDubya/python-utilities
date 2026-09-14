import pytest
import json
from app import app
from app.config import TestingConfig

@pytest.fixture
def client():
    app.config.from_object(TestingConfig)
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_join_queue(client):
    """Test joining the queue"""
    response = client.post('/queue',
                          json={'name': 'test_task'},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'position' in data
    assert data['position'] == 1

def test_check_position(client):
    """Test checking queue position"""
    # First join the queue
    client.post('/queue',
               json={'name': 'test_task'},
               content_type='application/json')

    # Then check position
    response = client.get('/queue/test_task')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['position'] == 1

def test_priority_queue(client):
    """Test priority queue ordering"""
    # Add tasks with different priorities
    client.post('/queue', json={'name': 'low_priority', 'priority': 0})
    client.post('/queue', json={'name': 'high_priority', 'priority': 10})
    client.post('/queue', json={'name': 'medium_priority', 'priority': 5})

    # Check that high priority is first
    response = client.get('/queue/high_priority')
    data = json.loads(response.data)
    assert data['position'] == 1

def test_next_in_queue(client):
    """Test getting next task from queue"""
    client.post('/queue', json={'name': 'task1'})
    client.post('/queue', json={'name': 'task2'})

    response = client.post('/queue/next')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['next'] == 'task1'
    assert data['remaining'] == 1

def test_list_queue(client):
    """Test listing all queue tasks"""
    client.post('/queue', json={'name': 'task1'})
    client.post('/queue', json={'name': 'task2'})

    response = client.get('/queue/list')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2
    assert len(data['queue']) == 2

def test_remove_from_queue(client):
    """Test removing a specific task"""
    client.post('/queue', json={'name': 'task_to_remove'})

    response = client.delete('/queue/remove/task_to_remove')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['task'] == 'task_to_remove'

def test_clear_queue(client):
    """Test clearing the entire queue"""
    client.post('/queue', json={'name': 'task1'})
    client.post('/queue', json={'name': 'task2'})

    response = client.post('/queue/clear')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['tasks_removed'] == 2

def test_metrics(client):
    """Test metrics endpoint"""
    client.post('/queue', json={'name': 'metric_task'})

    response = client.get('/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'metrics' in data
    assert data['metrics']['total_tasks'] >= 1

def test_invalid_request(client):
    """Test error handling for invalid requests"""
    response = client.post('/queue',
                          json={},
                          content_type='application/json')
    assert response.status_code == 400

def test_not_found_task(client):
    """Test checking position of non-existent task"""
    response = client.get('/queue/nonexistent')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['position'] == -1
    assert data['status'] == 'not_found'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
