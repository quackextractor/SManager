# manager.py
import datetime
import os
import shutil
import subprocess
import sys
import threading
import time
from typing import Optional, Dict

import schedule

# Import custom modules
from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.run_script import run_script
from utils.send_message import send_server_message


def load_latest_backup(backup_dir2):
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
        backup_dir = os.path.join(server_root, backup_dir2)

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
        stop_result = subprocess.run(['python3', os.path.join(base_dir, 'scripts', 'stop_mc.py')],
                                     capture_output=True)

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

class MinecraftServerManager:

    def __init__(self):
        # Setup base paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.base_dir, 'scripts')
        self.config_path = os.path.join(self.base_dir, 'config.ini')

        # Initialize config and logger
        self.config_manager = ConfigManager(self.config_path)
        self.logger = Logger(os.path.join(self.base_dir, 'ManagerLog.txt'))

        # Initialize scheduling
        self.scheduled_tasks: Dict[str, schedule.Job] = {}
        self.schedule_thread = None
        self.schedule_running = False

    def _run_script(self, script_name: str, log_message: Optional[str] = None) -> bool:
        """
        Run a script from the scripts directory.

        :param script_name: Name of the script to run.
        :param log_message: Optional log message to write.
        :return: True if script ran successfully, False otherwise.
        """
        return run_script(self.scripts_dir, script_name, self.logger, log_message)

    def send_server_message(self, message: str) -> bool:
        """
        Wrapper method to send a message/command to all active screen sessions.
        """
        return send_server_message(self.config_manager, message, self.logger)

    def start_all(self):
        """Start Minecraft server and Playit tunnel"""
        success = (
                self._run_script('start_tunnel.py', "Starting Playit tunnel") and
                self._run_script('start_mc.py', "Starting Minecraft server")
        )
        print("Start All: " + ("Success" if success else "Failed"))

    def stop_all(self):
        """Stop Minecraft server and Playit tunnel"""
        success = (
                self._run_script('stop_mc.py', "Stopping Minecraft server") and
                self._run_script('stop_tunnel.py', "Stopping Playit tunnel")
        )
        print("Stop All: " + ("Success" if success else "Failed"))

    def restart_all(self):
        """Restart Minecraft server and Playit tunnel"""
        self.stop_all()
        time.sleep(2)  # Short delay between stop and start
        self.start_all()

    def start_mc(self):
        """Start Minecraft server"""
        success = self._run_script('start_mc.py', "Starting Minecraft server")
        print("Start MC: " + ("Success" if success else "Failed"))

    def stop_mc(self):
        """Stop Minecraft server"""
        success = self._run_script('stop_mc.py', "Stopping Minecraft server")
        print("Stop MC: " + ("Success" if success else "Failed"))

    def restart_mc(self):
        """Restart Minecraft server"""
        self.stop_mc()
        time.sleep(2)  # Short delay between stop and start
        self.start_mc()

    def start_tunnel(self):
        """Start Playit tunnel"""
        success = self._run_script('start_tunnel.py', "Starting Playit tunnel")
        print("Start Tunnel: " + ("Success" if success else "Failed"))

    def stop_tunnel(self):
        """Stop Playit tunnel"""
        success = self._run_script('stop_tunnel.py', "Stopping Playit tunnel")
        print("Stop Tunnel: " + ("Success" if success else "Failed"))

    def restart_tunnel(self):
        """Restart Playit tunnel"""
        self.stop_tunnel()
        time.sleep(2)  # Short delay between stop and start
        self.start_tunnel()

    def backup(self):
        """Create Minecraft world backup"""
        success = self._run_script('backup.py', "Creating Minecraft world backup")
        print("Backup: " + ("Success" if success else "Failed"))

    def load_backup(self, milestone=False):
        backup_dir = 'milestone_backups' if milestone else 'backups'
        success = load_latest_backup(backup_dir)
        print("Load Backup: " + ("Success" if success else "Failed"))

    def show_log(self):
        """Show latest Minecraft server log"""
        log_path = os.path.join(self.config_manager.get_server_root(), 'logs', 'latest.log')
        try:
            with open(log_path, 'r') as log_file:
                print(log_file.read())
        except FileNotFoundError:
            print(f"Log file not found: {log_path}")

    def show_scheduled_tasks(self):
        """Display currently scheduled tasks."""
        if not self.scheduled_tasks:
            print("No scheduled tasks.")
            return

        print("Current Scheduled Tasks:")
        for task_id, job in self.scheduled_tasks.items():
            print(f"- Task ID: {task_id} (Next run in {job.next_run - datetime.datetime.now()})")

    def toggle_autobackup(self):
        """Toggle the autobackup setting and start/stop the backup schedule."""
        current_setting = self.config_manager.is_autobackup_enabled()
        new_setting = not current_setting
        self.config_manager.set_autobackup(new_setting)

        # Start or stop the backup schedule based on the new setting
        if new_setting:
            self._start_autobackup()
            print("Autobackup enabled.")
        else:
            self._stop_autobackup()
            print("Autobackup disabled.")

        self.logger.log(f"Autobackup {'enabled' if new_setting else 'disabled'}")

    def _start_autobackup(self):
        """Start scheduled autobackup if not already running."""
        if "autobackup" not in self.scheduled_tasks:
            # Get interval from config (default to 60 minutes if not set)
            autobackup_interval = int(self.config_manager.get('SERVER', 'autobackupinterval', fallback=60))

            # Schedule autobackup based on the interval from the config file
            job = schedule.every(autobackup_interval).minutes.do(self.backup).tag("autobackup")
            self.scheduled_tasks["autobackup"] = job
            print(f"Autobackup scheduled every {autobackup_interval} minutes.")
            self._start_schedule_thread()

    def _stop_autobackup(self):
        """Stop scheduled autobackup if it's running."""
        if "autobackup" in self.scheduled_tasks:
            schedule.cancel_job(self.scheduled_tasks["autobackup"])
            del self.scheduled_tasks["autobackup"]
            print("Autobackup schedule stopped.")

    def toggle_milestonebackup(self):
        """Toggle the milestone backup setting and start/stop the milestone backup schedule."""
        current_setting = self.config_manager.is_milestonebackup_enabled()
        new_setting = not current_setting
        self.config_manager.set_milestonebackup(new_setting)

        if new_setting:
            self._start_milestonebackup()
            print("Milestone backup enabled.")
        else:
            self._stop_milestonebackup()
            print("Milestone backup disabled.")

        self.logger.log(f"Milestone backup {'enabled' if new_setting else 'disabled'}")

    def _start_milestonebackup(self):
        """Start scheduled milestone backup if not already running."""
        if "milestonebackup" not in self.scheduled_tasks:
            milestonebackup_interval = self.config_manager.get_milestone_backup_interval()
            milestonebackup_dir = self.config_manager.get_milestone_backup_dir()

            # Schedule milestone backup based on interval from the config file
            job = schedule.every(milestonebackup_interval).minutes.do(self.milestone_backup).tag("milestonebackup")
            self.scheduled_tasks["milestonebackup"] = job
            print(f"Milestone backup scheduled every {milestonebackup_interval} minutes.")
            self._start_schedule_thread()

    def _stop_milestonebackup(self):
        """Stop scheduled milestone backup if it's running."""
        if "milestonebackup" in self.scheduled_tasks:
            schedule.cancel_job(self.scheduled_tasks["milestonebackup"])
            del self.scheduled_tasks["milestonebackup"]
            print("Milestone backup schedule stopped.")

    def milestone_backup(self):
        """Create a milestone backup without a max backup limit."""
        milestonebackup_dir = self.config_manager.get_milestone_backup_dir()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(milestonebackup_dir, f"milestone_backup_{timestamp}")
        os.makedirs(milestonebackup_dir, exist_ok=True)

        success = shutil.copytree(os.path.join(self.config_manager.get_server_root(), 'world'), backup_path)
        self.logger.log(f"Milestone backup created: {backup_path}")



    def warn_and_schedule_stop_all(self, delay_minutes: int):
        """
        Warn players about an upcoming server shutdown and then schedule the stop.

        :param delay_minutes: Number of minutes to wait before stopping.
        """
        warning_message = f"Server will shutdown in {delay_minutes} minutes. Please prepare to log out."

        # Send the warning message to all active screen sessions
        if not self.send_server_message(warning_message):
            self.logger.log("Failed to send warning message to any active screen session.")

        # Schedule the server stop
        self.schedule_stop_all(delay_minutes)

        log_message = f"Warned players and scheduled server stop in {delay_minutes} minutes."
        print(log_message)
        self.logger.log(log_message)

    def schedule_stop_all(self, delay_minutes: int):
        """
        Schedule stopping the Minecraft server and Playit tunnel.
        
        :param delay_minutes: Number of minutes to wait before stopping
        """

        def scheduled_stop():
            self.stop_all()
            # Cancel this job after it runs
            if task_id in self.scheduled_tasks:
                schedule.cancel_job(self.scheduled_tasks[task_id])
                del self.scheduled_tasks[task_id]
                print(f"Scheduled stop task completed and removed: {task_id}")

        # Schedule the job to run once after delay_minutes
        task_id = f'sqa_{delay_minutes}'
        job = schedule.every(delay_minutes).minutes.do(scheduled_stop).tag(task_id)
        self.scheduled_tasks[task_id] = job

        print(f"Scheduled server stop in {delay_minutes} minutes")
        self.logger.log(f"Scheduled server stop in {delay_minutes} minutes")

        # Start the scheduling thread if not already running
        self._start_schedule_thread()

    def _start_schedule_thread(self):
        """Start the thread that runs scheduled jobs."""
        if not self.schedule_running:
            self.schedule_running = True

            def run_schedule():
                while self.schedule_running:
                    schedule.run_pending()
                    time.sleep(1)

            # Create and start the thread
            self.schedule_thread = threading.Thread(target=run_schedule)
            self.schedule_thread.daemon = True
            self.schedule_thread.start()
            print("Scheduling thread started.")

    def stop_schedule_thread(self):
        """Stop the scheduling thread."""
        self.schedule_running = False
        if self.schedule_thread:
            self.schedule_thread.join()
            self.schedule_thread = None
            print("Scheduling thread stopped.")

    def help(self):
        """Display help information about commands."""
        help_text = """
Minecraft Server Manager Commands:
- sa           : Start Minecraft server and Playit tunnel
- qa           : Stop Minecraft server and Playit tunnel
- ra           : Restart Minecraft server and Playit tunnel
- smc          : Start Minecraft server
- qmc          : Stop Minecraft server
- rmc          : Restart Minecraft server
- st           : Start Playit tunnel
- qt           : Stop Playit tunnel
- rt           : Restart Playit tunnel
- backup       : Create Minecraft world backup
- backup -m    : Create world milestone backup
- load         : Load latest backup
- load -m      : Load latest milestonebackup
- log          : Show latest server log
- auto         : Toggle autobackup
- auto -m      : Toggle milestonebackup
- sqa <minutes>: Schedule server stop after a delay
- wsqa <minutes>: Warn players and schedule stop after a delay
- rs <task_id> : Remove a scheduled task by ID
- ss           : Show scheduled tasks
- s <txt>  : Send a message to console (/say is added) 
                 or a command (if it's already starting with /)

- help         : Show this help message
- exit         : Exit the program
"""
        print(help_text)
        self.logger.log("Displayed help information")


def main():
    manager = MinecraftServerManager()

    # Check if autobackup is enabled in config and start it if necessary
    if manager.config_manager.is_autobackup_enabled():
        manager._start_autobackup()
        print("Autobackup enabled from config.")

    print("Minecraft Server Manager")
    manager.help()

    while True:
        try:
            command_input = input("Enter command (or 'help' for options): ").strip().lower()
            parts = command_input.split()
            command = parts[0]

            # Command handling
            if command == 'sa':
                manager.start_all()
            elif command == 'qa':
                manager.stop_all()
            elif command == 'ra':
                manager.restart_all()
            elif command == 'smc':
                manager.start_mc()
            elif command == 'qmc':
                manager.stop_mc()
            elif command == 'rmc':
                manager.restart_mc()
            elif command == 'st':
                manager.start_tunnel()
            elif command == 'qt':
                manager.stop_tunnel()
            elif command == 'rt':
                manager.restart_tunnel()
            elif command == 'backup':
                if len(parts) > 1 and parts[1] == '-m':
                    manager.milestone_backup()
                else:
                    manager.backup()
            elif command == 'load':
                manager.load_backup(milestone=(len(parts) > 1 and parts[1] == '-m'))
            elif command == 'log':
                manager.show_log()
            elif command == 'auto':
                if len(parts) > 1 and parts[1] == '-m':
                    manager.toggle_milestonebackup()
                else:
                    manager.toggle_autobackup()
            elif command == 'sqa' and len(parts) == 2 and parts[1].isdigit():
                manager.schedule_stop_all(int(parts[1]))
            elif command == 'wsqa' and len(parts) == 2 and parts[1].isdigit():
                manager.warn_and_schedule_stop_all(int(parts[1]))
            elif command == 'rs' and len(parts) == 2:
                task_id = parts[1]
                if task_id in manager.scheduled_tasks:
                    schedule.cancel_job(manager.scheduled_tasks[task_id])
                    del manager.scheduled_tasks[task_id]
                    print(f"Removed scheduled task: {task_id}")
                else:
                    print(f"No such scheduled task: {task_id}")
            elif command == 's' and len(parts) >= 2:
                message_body = " ".join(parts[1:])
                manager.send_server_message(message_body)
            elif command == 'ss':
                manager.show_scheduled_tasks()
            elif command == 'help':
                manager.help()
            elif command == 'exit':
                manager.stop_schedule_thread()
                print("Exiting Minecraft Server Manager.")
                sys.exit()
            else:
                print("Unknown command. Type 'help' for a list of commands.")

        except Exception as e:
            print(f"An error occurred: {e}")
            manager.logger.log(f"Error in main loop: {e}")


if __name__ == "__main__":
    main()