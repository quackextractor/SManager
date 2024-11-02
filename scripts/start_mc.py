# scripts/start_mc.py
import os
import subprocess
import sys
import time

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger


def start_minecraft_server():
    # Get the server directory from environment or hardcode
    server_dir = os.path.expanduser("~/Desktop/Fabric")
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ManagerLog.txt')

    logger = Logger(log_path)

    try:

        # Log active screen sessions
        try:
            screen_sessions = subprocess.check_output(['screen', '-ls'], stderr=subprocess.STDOUT, text=True)
            logger.log("Active Screen Sessions:\n" + screen_sessions.strip())
        except subprocess.CalledProcessError:
            logger.log("Could not list screen sessions")

        # Start Minecraft server in a visible screen session
        subprocess.run([
            'gnome-terminal',
            '--',
            'screen',
            '-S',
            'minecraftScreen',
            'bash',
            '-c',
            f'cd "{server_dir}" && java -Xmx16G -jar fabric-server.jar nogui; exec bash'
        ], check=True)

        # Delay to allow server to start
        time.sleep(15)

        logger.log("Minecraft server started in visible screen session")
        return True
    except Exception as e:
        logger.log(f"Failed to start Minecraft server: {e}")
        return False


if __name__ == "__main__":
    start_minecraft_server()
