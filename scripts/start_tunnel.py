# scripts/start_tunnel.py
import os
import subprocess
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger


def start_playit_tunnel():
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ManagerLog.txt')

    logger = Logger(log_path)

    try:
        # Start Playit tunnel in a new terminal
        subprocess.run([
            'gnome-terminal',
            '--',
            'bash',
            '-c',
            'playit; exec bash'
        ], check=True)

        logger.log("Playit tunnel started successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.log(f"Failed to start Playit tunnel: {e}")
        return False


if __name__ == "__main__":
    start_playit_tunnel()
