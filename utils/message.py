import os
import re
import subprocess
import sys
import time


def send_server_message(message: str) -> bool:
    """
    Send a message/command to all active screen sessions and log the last few lines of the server log.

    Args:
        message (str): The message/command to send.

    Returns:
        bool: True if the message was sent successfully to at least one session.
    """
    try:
        # Get list of screen sessions
        screen_list_output = subprocess.check_output(['screen', '-ls'], universal_newlines=True)
        screen_sessions = re.findall(r'\t(\d+\.\S+)', screen_list_output)

        if not screen_sessions:
            print("No active screen sessions found.")
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
                print(f"Message sent to session {session}: {message}")

            except subprocess.CalledProcessError as cmd_err:
                print(f"Failed to send message to {session}: {cmd_err}")
            except subprocess.TimeoutExpired:
                print(f"Timeout sending message to {session}")

        time.sleep(0.5)

        # Log the last few lines of the server log
        log_path = os.path.join('logs', 'latest.log')
        try:
            with open(log_path, 'r') as log_file:
                last_lines = log_file.readlines()[-2:]  # Get the last few lines

                print("Last few lines of the server log:")
                for line in last_lines:
                    print(line.strip())

        except FileNotFoundError:
            print(f"Log file not found: {log_path}")

        return success

    except Exception as e:
        print(f"Error in send_server_message: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 message.py 'text'")
        sys.exit(1)

    message = sys.argv[1]
    if not send_server_message(message):
        sys.exit(1)
