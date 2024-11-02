# scripts/backup.py
import os
import shutil
import sys
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger
from utils.config_manager import ConfigManager


def create_minecraft_backup():
    # Get config and log paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.ini')
    log_path = os.path.join(base_dir, 'ManagerLog.txt')

    # Initialize config manager and logger
    config_manager = ConfigManager(config_path)
    logger = Logger(log_path)

    # Get server root and max backups from config
    server_root = config_manager.get_server_root()
    max_backups = config_manager.get_max_world_backups()

    try:
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(server_root, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamp for backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"world_backup_{timestamp}"

        # Full paths
        world_path = os.path.join(server_root, 'world')
        backup_path = os.path.join(backup_dir, backup_name)

        # Perform backup
        shutil.copytree(world_path, backup_path)
        logger.log(f"Minecraft world backup created: {backup_name}")

        # Enforce max backups by removing the oldest if necessary
        backups = sorted(os.listdir(backup_dir))
        if len(backups) > max_backups:
            oldest_backup = os.path.join(backup_dir, backups[0])
            shutil.rmtree(oldest_backup)
            logger.log(f"Oldest backup removed: {backups[0]}")

        return True
    except Exception as e:
        logger.log(f"Failed to create Minecraft world backup: {e}")
        return False


if __name__ == "__main__":
    create_minecraft_backup()
