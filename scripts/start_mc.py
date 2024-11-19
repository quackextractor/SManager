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
        except subprocess.CalledProcessError as e:
            if e.returncode == 1 and "No Sockets found" in e.output:
                logger.log("No active screen sessions")
            else:
                logger.log(f"Error checking screen sessions: {e}")

        # Check if the screen session already exists
        try:
            subprocess.check_output(['screen', '-S', 'minecraftScreen', '-Q', 'select', '.'], stderr=subprocess.STDOUT)
            logger.log("Screen session 'minecraftScreen' already exists")
            return False
        except subprocess.CalledProcessError:
            pass  # Screen session doesn't exist, which is what we want

        # Create a new detached screen session and start the Minecraft server
        start_command = f'cd "{server_root}" && java -Xmx16G -jar fabric-server.jar nogui'
        subprocess.run([
            'screen',
            '-dmS',  # Start as a detached session
            'minecraftScreen',
            'bash',
            '-c',
            start_command
        ], check=True)

        # Delay to allow server to start
        time.sleep(15)

        # Verify the screen session is running
        try:
            screen_sessions = subprocess.check_output(['screen', '-ls'], stderr=subprocess.STDOUT, text=True)
            if 'minecraftScreen' in screen_sessions:
                logger.log("Minecraft server started successfully in screen session")
                return True
            else:
                logger.log("Screen session not found after starting server")
                return False
        except subprocess.CalledProcessError as e:
            logger.log(f"Error verifying screen session: {e}")
            return False

    except Exception as e:
        logger.log(f"Failed to start Minecraft server: {e}")
        return False


def attach_to_server():
    """
    Utility function to attach to the Minecraft server screen session.
    Can be called separately to connect to the running server.
    """
    try:
        subprocess.run(['screen', '-r', 'minecraftScreen'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to attach to screen session: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "attach":
        attach_to_server()
    else:
        start_minecraft_server()