# utils/send_message.py
import os
import re
import subprocess
import time

from utils.config_manager import ConfigManager
from utils.logger import Logger


def send_server_message(config_manager: ConfigManager, message: str, logger: Logger = None) -> bool:
    """
    Send a message/command to all active screen sessions and log the last few lines of the server log.

    Args:
        config_manager (ConfigManager): ConfigManager instance to access server root.
        message (str): The message/command to send.
        logger (Logger, optional): Logger instance for logging errors.

    Returns:
        bool: True if message was sent successfully to at least one session.
    """
    try:
        # Get list of screen sessions
        screen_list_output = subprocess.check_output(['screen', '-ls'], universal_newlines=True)
        screen_sessions = re.findall(r'\t(\d+\.\S+)', screen_list_output)

        if not screen_sessions:
            if logger:
                logger.log("No active screen sessions found")
            return False

        success = False
        for session in screen_sessions:
            try:
                # If message doesn't start with '/', assume it's a chat message
                cmd = message if message.startswith('/') else f'/say {message}'

                # Send command to screen session
                subprocess.run([
                    'screen',
                    '-S',
                    session,
                    '-X',
                    'stuff',
                    f'\n{cmd}\n'
                ], check=True, timeout=3)

                success = True
                if logger:
                    logger.log(f"Message sent to session {session}: {message}")

            except subprocess.CalledProcessError as cmd_err:
                if logger:
                    logger.log(f"Failed to send message to {session}: {cmd_err}")
            except subprocess.TimeoutExpired:
                if logger:
                    logger.log(f"Timeout sending message to {session}")

        time.sleep(0.5)
        # Log the last few lines of the server log
        log_path = os.path.join(config_manager.get_server_root(), 'logs', 'latest.log')
        try:
            with open(log_path, 'r') as log_file:
                last_lines = log_file.readlines()[-2:]  # Get the last few lines

                # Print and log each line
                print("Last few lines of the server log:")
                for line in last_lines:
                    print(line.strip())  # Print to console
                    if logger:
                        logger.log(line.strip())  # Log each line without extra newlines

        except FileNotFoundError:
            if logger:
                logger.log(f"Log file not found: {log_path}")

        return success

    except Exception as e:
        if logger:
            logger.log(f"Error in send_server_message: {e}")
        return False
