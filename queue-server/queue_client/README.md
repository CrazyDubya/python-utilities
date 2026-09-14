# Queue Client

This Python module provides a decorator to manage function execution through a queue. It communicates with a Flask-based web server that manages the queue.

## Setup

1. Install the required packages:

    ```bash
    pip install requests
    ```

2. Run the Flask server for queue management:

    ```bash
    cd queue_server
    FLASK_APP=run.py flask run
    ```

## Usage

1. Import the `queue_decorator` from `queue.py`.

    ```python
    from queue import queue_decorator
    ```

2. Use the decorator to wrap around any function you want to queue:

    ```python
    @queue_decorator('example_task')
    def example_task():
        print('Task is running...')
        time.sleep(10)  # Simulate a long-running task
        print('Task is complete.')

    if __name__ == '__main__':
        example_task()
    ```

3. Run your script:

    ```bash
    python queue.py
    ```

The function will join the queue and run when its turn comes.

## Notes

- The `QUEUE_SERVER_URL` is set to `http://127.0.0.1:5000` by default. Update it if your server is running on a different URL or port.
- The example provided simulates a long-running task. Replace it with your actual function logic.
