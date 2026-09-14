import time
import requests

QUEUE_SERVER_URL = 'http://127.0.0.1:5000'

def queue_decorator(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Join the queue
            response = requests.post(f'{QUEUE_SERVER_URL}/queue', json={'name': name})
            position = response.json()['position']
            print(f'{name} is at position {position} in the queue.')

            # Poll the queue until it is this function's turn
            while position != 1:
                time.sleep(5)
                response = requests.get(f'{QUEUE_SERVER_URL}/queue/{name}')
                position = response.json()['position']
                print(f'{name} is at position {position} in the queue.')
            
            # It's this function's turn
            print(f'{name} is now running.')

            result = func(*args, **kwargs)

            # Notify the server that this function has completed
            requests.post(f'{QUEUE_SERVER_URL}/queue/next')
            
            return result
        return wrapper
    return decorator

# Example usage
@queue_decorator('example_task')
def example_task():
    print('Task is running...')
    time.sleep(10)  # Simulate a long-running task
    print('Task is complete.')

if __name__ == '__main__':
    example_task()
