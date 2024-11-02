# scripts/stop_mc.py
import os
import re
import subprocess
import sys
import time

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger


def stop_all_screens():
    # Path for logging
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ManagerLog.txt')
    logger = Logger(log_path)

    try:
        # Get list of all screen sessions
        screen_list_output = subprocess.check_output(['screen', '-ls'], universal_newlines=True)

        # Extract screen session names using regex
        screen_sessions = re.findall(r'\t(\d+\.\S+)', screen_list_output)

        logger.log(f"Found {len(screen_sessions)} screen sessions")

        # Iterate through each screen session
        for session in screen_sessions:
            try:
                # Try to send stop command (useful for Minecraft-like servers)
                subprocess.run([
                    'screen',
                    '-S',
                    session,
                    '-X',
                    'stuff',
                    '\nstop\n'
                ], check=True, timeout=3)

                logger.log(f"Sent stop command to session {session}")
            except subprocess.CalledProcessError as cmd_err:
                logger.log(f"Failed to send stop command to {session}: {cmd_err}")
            except subprocess.TimeoutExpired:
                logger.log(f"Timeout sending stop command to {session}")

        # Wait a bit to allow graceful shutdown
        time.sleep(3)

        # Kill all screen sessions
        subprocess.run(['killall', 'screen'], check=True)

        logger.log("All screen sessions killed")
        return True

    except Exception as e:
        logger.log(f"Error stopping screen sessions: {e}")
        return False


if __name__ == "__main__":
    stop_all_screens()
