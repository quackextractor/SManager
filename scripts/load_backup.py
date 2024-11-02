# scripts/load_backup.py
import os
import shutil
import subprocess
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger
from utils.config_manager import ConfigManager


def load_latest_backup():
    # Get config and log paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.ini')
    log_path = os.path.join(base_dir, 'ManagerLog.txt')

    # Initialize config manager and logger
    config_manager = ConfigManager(config_path)
    logger = Logger(log_path)

    # Get server root from config
    server_root = config_manager.get_server_root()

    try:
        # Find latest backup
        backup_dir = os.path.join(server_root, 'backups')

        # Get all backup folders, sort by name (which includes timestamp)
        backups = sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))])

        if not backups:
            logger.log("No backups found.")
            return False

        # Get the latest backup
        latest_backup = backups[-1]
        latest_backup_path = os.path.join(backup_dir, latest_backup)
        world_path = os.path.join(server_root, 'world')

        # Stop Minecraft server (assuming stop_mc.py script exists)
        stop_result = subprocess.run(['python3', os.path.join(base_dir, 'scripts', 'stop_mc.py')], capture_output=True)

        # Remove existing world
        if os.path.exists(world_path):
            shutil.rmtree(world_path)

        # Copy backup to world directory
        shutil.copytree(latest_backup_path, world_path)

        logger.log(f"Loaded latest backup: {latest_backup}")
        return True
    except Exception as e:
        logger.log(f"Failed to load latest backup: {e}")
        return False


if __name__ == "__main__":
    load_latest_backup()
