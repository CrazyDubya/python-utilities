"""
Enhanced Queue Client with advanced features
"""
import time
import requests
import logging
from typing import Callable, Optional, Any
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueueClient:
    """Enhanced queue client with retry logic, timeouts, and better error handling"""

    def __init__(self,
                 server_url: str = 'http://127.0.0.1:5000',
                 api_key: Optional[str] = None,
                 poll_interval: int = 5,
                 timeout: int = 3600):
        self.server_url = server_url
        self.api_key = api_key
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.headers = {'X-API-Key': api_key} if api_key else {}

    def queue_decorator(self, name: str, priority: int = 0, max_retries: int = 3):
        """
        Decorator to queue function execution

        Args:
            name: Task name
            priority: Task priority (higher = runs sooner)
            max_retries: Number of retries on failure
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                retries = 0
                while retries <= max_retries:
                    try:
                        # Join the queue
                        response = requests.post(
                            f'{self.server_url}/queue',
                            json={'name': name, 'priority': priority},
                            headers=self.headers,
                            timeout=10
                        )
                        response.raise_for_status()

                        data = response.json()
                        position = data['position']
                        queue_size = data.get('queue_size', 'unknown')

                        logger.info(f'{name} joined queue at position {position} (queue size: {queue_size})')

                        # Poll the queue until it's our turn
                        start_time = time.time()
                        while position != 1:
                            # Check timeout
                            if time.time() - start_time > self.timeout:
                                logger.error(f'{name} timed out waiting in queue')
                                self._remove_from_queue(name)
                                raise TimeoutError(f'Task {name} timed out after {self.timeout} seconds')

                            time.sleep(self.poll_interval)

                            try:
                                response = requests.get(
                                    f'{self.server_url}/queue/{name}',
                                    headers=self.headers,
                                    timeout=10
                                )
                                response.raise_for_status()

                                data = response.json()
                                position = data['position']

                                if position == -1:
                                    logger.warning(f'{name} was removed from queue')
                                    raise RuntimeError(f'Task {name} was removed from queue')

                                logger.info(f'{name} at position {position}')

                            except requests.RequestException as e:
                                logger.warning(f'Error checking position: {e}')
                                # Continue polling even if one check fails
                                continue

                        # It's our turn!
                        logger.info(f'{name} is now running')

                        # Execute the function
                        result = func(*args, **kwargs)

                        # Notify completion
                        try:
                            requests.post(
                                f'{self.server_url}/queue/next',
                                headers=self.headers,
                                timeout=10
                            )
                            logger.info(f'{name} completed successfully')
                        except requests.RequestException as e:
                            logger.warning(f'Failed to notify completion: {e}')

                        return result

                    except requests.RequestException as e:
                        retries += 1
                        if retries > max_retries:
                            logger.error(f'{name} failed after {max_retries} retries: {e}')
                            raise
                        logger.warning(f'{name} failed, retrying ({retries}/{max_retries}): {e}')
                        time.sleep(2 ** retries)  # Exponential backoff

                    except Exception as e:
                        logger.error(f'{name} encountered an error: {e}')
                        self._remove_from_queue(name)
                        raise
                
                # If we exit the retry loop without success, raise an error
                raise RuntimeError(f'Task {name} failed after {max_retries} retries')

            return wrapper
        return decorator

    def _remove_from_queue(self, name: str):
        """Remove a task from the queue"""
        try:
            requests.delete(
                f'{self.server_url}/queue/remove/{name}',
                headers=self.headers,
                timeout=10
            )
        except requests.RequestException as e:
            logger.warning(f'Failed to remove task from queue: {e}')

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        try:
            response = requests.get(
                f'{self.server_url}/queue/list',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'Failed to get queue status: {e}')
            return {'error': str(e)}

    def get_metrics(self) -> dict:
        """Get queue metrics"""
        try:
            response = requests.get(
                f'{self.server_url}/metrics',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'Failed to get metrics: {e}')
            return {'error': str(e)}

    def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            response = requests.get(
                f'{self.server_url}/health',
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('status') == 'healthy'
        except requests.RequestException:
            return False


# Default client instance
QUEUE_SERVER_URL = 'http://127.0.0.1:5000'
default_client = QueueClient(QUEUE_SERVER_URL)

def queue_decorator(name: str, priority: int = 0):
    """Convenience function using default client"""
    return default_client.queue_decorator(name, priority)


# Example usage
if __name__ == '__main__':
    # Create a client
    client = QueueClient('http://127.0.0.1:5000')

    # Example 1: Basic usage
    @client.queue_decorator('example_task')
    def example_task():
        print('Task is running...')
        time.sleep(10)
        print('Task is complete.')
        return 'success'

    # Example 2: High priority task
    @client.queue_decorator('urgent_task', priority=10)
    def urgent_task():
        print('Urgent task running!')
        return 'urgent_complete'

    # Example 3: Check server health
    if client.health_check():
        print('Server is healthy')

        # Run tasks
        result1 = example_task()
        print(f'Result: {result1}')

        # Get queue status
        status = client.get_queue_status()
        print(f'Queue status: {status}')

        # Get metrics
        metrics = client.get_metrics()
        print(f'Metrics: {metrics}')
    else:
        print('Server is not available')
