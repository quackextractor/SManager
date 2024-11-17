# utils/config_manager.py
import configparser
import os


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            # Create default configuration
            self.config['SERVER'] = {
                'AutoBackupInterval': '10',
                'IsAutoBackupEnabled': 'False',
                'ServerRootLocation': '/home/miro/Desktop/Fabric',
                'MaxWorldBackups': '10',
                'milestonebackupinterval': '120',
                'milestonebackupdir': '/home/miro/Desktop/Fabric/milestone_backups',
                'IsMilestoneBackupEnabled': 'False'
            }
            self._save_config()

    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def get_autobackup_interval(self) -> int:
        """Get autobackup interval in minutes"""
        return self.config.getint('SERVER', 'AutoBackupInterval')

    def is_autobackup_enabled(self) -> bool:
        """Check if autobackup is enabled"""
        return self.config.getboolean('SERVER', 'IsAutoBackupEnabled')

    def set_autobackup(self, enabled: bool):
        """Set autobackup status"""
        self.config.set('SERVER', 'IsAutoBackupEnabled', str(enabled))
        self._save_config()

    def get_max_world_backups(self) -> int:
        """Get the maximum number of backups to retain."""
        return self.config.getint('SERVER', 'MaxWorldBackups', fallback=10)

    def get_server_root(self) -> str:
        """Get server root location"""
        return self.config.get('SERVER', 'ServerRootLocation')

    def get_milestone_backup_interval(self) -> int:
        """Get milestone backup interval in minutes"""
        return self.config.getint('SERVER', 'milestonebackupinterval', fallback=1440)

    def get_milestone_backup_dir(self) -> str:
        """Get milestone backup directory"""
        return self.config.get('SERVER', 'milestonebackupdir', fallback='/home/miro/Desktop/Fabric/milestone_backups')

    def is_milestonebackup_enabled(self) -> bool:
        """Check if milestone backup is enabled"""
        return self.config.getboolean('SERVER', 'IsMilestoneBackupEnabled')

    def set_milestonebackup(self, enabled: bool):
        """Set milestone backup status"""
        self.config.set('SERVER', 'IsMilestoneBackupEnabled', str(enabled))
        self._save_config()

    def get(self, section: str, option: str, fallback=None):
        """
        General method to retrieve a value from the config with an optional fallback.

        :param section: The section in the config file (e.g., 'SERVER')
        :param option: The specific setting to retrieve
        :param fallback: The default value if the setting is not found
        :return: The setting's value or the fallback
        """
        return self.config.get(section, option, fallback=fallback)
