import logging
import threading
import time
import os

# Shared log file name for all scripts (can be overridden if needed)
LOG_FILE = "sentinal_logs.log"

def log_and_print(message, level='info', log_file=LOG_FILE):
    """
    Helper function to log and print messages.
    Configures logging to the specified log_file if not already set.
    Args:
        message (str): The message to log and print.
        level (str): Logging level ('info', 'error', 'warning', 'debug').
        log_file (str): Path to the log file.
    """
    print(message)
    logger = logging.getLogger(log_file)
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    if level == 'info':
        logger.info(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.debug(message)

def spinner(stop_event, message="Processing"):
    """
    Displays a spinner/loading indicator in the terminal.
    Usage:
        stop_event = threading.Event()
        t = threading.Thread(target=spinner, args=(stop_event, "Message"))
        t.start()
        ... # do work
        stop_event.set()
        t.join()
    """
    spinner_chars = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        print(f"\r{message}... {spinner_chars[idx % len(spinner_chars)]}", end='', flush=True)
        idx += 1
        time.sleep(0.1)
    print("\r" + " " * (len(message) + 6) + "\r", end='', flush=True)  # Clear the line 