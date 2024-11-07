import os
import subprocess
import sys
import time

# Add parent directory to path to import utils
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
from utils.logger import Logger
from utils.config_manager import ConfigManager


def start_minecraft_server():
    # Get config and log paths
    config_path = os.path.join(base_dir, 'config.ini')
    log_path = os.path.join(base_dir, 'ManagerLog.txt')

    # Initialize config manager and logger
    config_manager = ConfigManager(config_path)
    logger = Logger(log_path)

    try:
        # Get server root from config
        server_root = config_manager.get_server_root()

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
            f'cd "{server_root}" && java -Xmx16G -jar fabric-server.jar nogui; exec bash'
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