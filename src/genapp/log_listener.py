# src/genapp/log_listener.py
import logging
import logging.config
from logging.handlers import QueueListener, RotatingFileHandler
from queue import Queue
import atexit
import threading
from django.conf import settings

# This queue will be shared between the main application and the listener thread
log_queue = Queue()

def start_log_listener():
    """
    Configures and starts a QueueListener in a background daemon thread.
    """
    # Create handler instances for the listener from settings
    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(
        filename=settings.BASE_DIR / '..' / 'logs' / 'application.log',
        maxBytes=1024 * 1024 * 5,
        backupCount=5
    )
    
    formatter = logging.Formatter(
        settings.LOGGING['formatters']['standard']['format']
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Create the listener
    listener = QueueListener(log_queue, console_handler, file_handler)

    # Start the listener in a daemon thread
    listener_thread = threading.Thread(target=listener.start, daemon=True)
    listener_thread.start()

    # Ensure the listener is stopped when the application exits
    atexit.register(listener.stop)
