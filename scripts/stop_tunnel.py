# scripts/stop_tunnel.py
import os
import subprocess
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger


def stop_playit_tunnel():
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ManagerLog.txt')

    logger = Logger(log_path)

    try:
        # Find and kill Playit process
        subprocess.run(['pkill', '-f', 'playit'], check=True)

        logger.log("Playit tunnel stopped successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.log(f"Failed to stop Playit tunnel: {e}")
        return False


if __name__ == "__main__":
    stop_playit_tunnel()
