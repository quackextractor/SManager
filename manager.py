# manager.py

import datetime
import os
import shutil
import subprocess
import sys
import threading
import time
from typing import Optional, Dict, Any, Callable

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

        # Command mapping for scheduling
        self.command_map: Dict[str, Callable[..., Any]] = {
            'sa': self.start_all,
            'qa': self.stop_all,
            'ra': self.restart_all,
            'smc': self.start_mc,
            'qmc': self.stop_mc,
            'rmc': self.restart_mc,
            'st': self.start_tunnel,
            'qt': self.stop_tunnel,
            'rt': self.restart_tunnel,
            'backup': self.backup,
            'backup -m': self.milestone_backup,
            'load': self.load_regular_backup,
            'load -m': self.load_milestone_backup,
            'log': self.show_log,
            'auto': self.toggle_autobackup,
            'auto -m': self.toggle_milestonebackup,
            'sas': self.set_shutdown_time,
            'tas': self.toggle_auto_shutdown,
        }

    def _run_script(self, script_name: str, log_message: Optional[str] = None) -> bool:
        """
        Run a script from the scripts directory.
        """
        return run_script(self.scripts_dir, script_name, self.logger, log_message)

    def send_server_message(self, message: str) -> bool:
        """
        Send a message/command to all active screen sessions.
        """
        return send_server_message(self.config_manager, message, self.logger)

    def _schedule_auto_shutdown(self):
        """Schedule the auto-shutdown task based on configured time"""
        if "auto_shutdown" in self.scheduled_tasks:
            schedule.cancel_job(self.scheduled_tasks["auto_shutdown"])
            del self.scheduled_tasks["auto_shutdown"]

        if not self.config_manager.is_auto_shutdown_enabled():
            return

        shutdown_time = self.config_manager.get_auto_shutdown_time()

        def shutdown_task():
            # Send warning message 5 minutes before shutdown
            self.send_server_message("Server will automatically shut down in 5 minutes!")
            time.sleep(300)  # Wait 5 minutes

            # Stop Minecraft server
            self.stop_mc()
            time.sleep(30)  # Wait for server to fully stop

            # Shutdown Linux system
            self.logger.log("Initiating system shutdown")
            os.system('sudo shutdown now')

        # Schedule the job to run daily at the specified time
        job = schedule.every().day.at(shutdown_time).do(shutdown_task).tag("auto_shutdown")
        self.scheduled_tasks["auto_shutdown"] = job
        self._start_schedule_thread()

        self.logger.log(f"Auto-shutdown scheduled for {shutdown_time}")

    def toggle_auto_shutdown(self):
        """Toggle the auto-shutdown setting"""
        current_setting = self.config_manager.is_auto_shutdown_enabled()
        new_setting = not current_setting
        self.config_manager.set_auto_shutdown(new_setting)

        if new_setting:
            self._schedule_auto_shutdown()
            print(f"Auto-shutdown enabled at {self.config_manager.get_auto_shutdown_time()}")
        else:
            if "auto_shutdown" in self.scheduled_tasks:
                schedule.cancel_job(self.scheduled_tasks["auto_shutdown"])
                del self.scheduled_tasks["auto_shutdown"]
            print("Auto-shutdown disabled")

        self.logger.log(f"Auto-shutdown {'enabled' if new_setting else 'disabled'}")

    def set_shutdown_time(self, time_str: str):
        """Set the auto-shutdown time"""
        if self.config_manager.set_auto_shutdown_time(time_str):
            if self.config_manager.is_auto_shutdown_enabled():
                self._schedule_auto_shutdown()
            print(f"Auto-shutdown time set to {time_str}")
            self.logger.log(f"Auto-shutdown time set to {time_str}")
            return True
        else:
            print("Invalid time format. Use HH:MM in 24-hour format (e.g., 23:30)")
            return False

    def schedule_command(self, command: str, delay_minutes: int, *args) -> bool:
        """
        Schedule any command to run after a specified delay.

        :param command: Command to schedule
        :param delay_minutes: Minutes to wait before executing
        :param args: Additional arguments for the command
        :return: True if scheduling successful, False otherwise
        """
        try:
            if command not in self.command_map and not (command.startswith('s ') or command == 'sqa'):
                print(f"Cannot schedule unknown command: {command}")
                return False

            def scheduled_execution():
                if command in self.command_map:
                    self.command_map[command](*args)
                elif command.startswith('s '):
                    # Handle server message command
                    message = " ".join(args)
                    self.send_server_message(message)
                elif command == 'sqa':
                    # Handle stop after delay
                    self.stop_all()

                # Remove the scheduled task after execution
                if task_id in self.scheduled_tasks:
                    schedule.cancel_job(self.scheduled_tasks[task_id])
                    del self.scheduled_tasks[task_id]

            # Create unique task ID
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            task_id = f'{command}_{timestamp}'

            # Schedule the job
            job = schedule.every(delay_minutes).minutes.do(scheduled_execution).tag(task_id)
            self.scheduled_tasks[task_id] = job

            # Start the scheduling thread if not already running
            self._start_schedule_thread()

            print(f"Scheduled {command} to run in {delay_minutes} minutes (Task ID: {task_id})")
            self.logger.log(f"Scheduled command: {command} for {delay_minutes} minutes later")
            return True

        except Exception as e:
            print(f"Failed to schedule command: {e}")
            self.logger.log(f"Failed to schedule command {command}: {e}")
            return False

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

    def backup(self, milestone=False):  # Fixed: Added milestone parameter
        """Create Minecraft world backup"""
        if milestone:
            self.milestone_backup()
        else:
            success = self._run_script('backup.py', "Creating Minecraft world backup")
            print("Backup: " + ("Success" if success else "Failed"))

    def load_backup(self, milestone=False):
        backup_dir = 'milestone_backups' if milestone else 'backups'
        success = load_latest_backup(backup_dir)
        print("Load Backup: " + ("Success" if success else "Failed"))

    def load_regular_backup(self, *args):  # Fixed: Added method to handle regular backup loading
        """Load the latest regular backup"""
        self.load_backup(False)

    def load_milestone_backup(self, *args):  # Fixed: Added method to handle milestone backup loading
        """Load the latest milestone backup"""
        self.load_backup(True)

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

    def handle_command(self, command_input: str) -> bool:
        """
        Handle command input including scheduling syntax.
        """
        try:
            parts = command_input.strip().split()
            if not parts:
                return False

            # Check for scheduling syntax: command -s minutes
            if len(parts) >= 3 and parts[-2] == '-s' and parts[-1].isdigit():
                delay_minutes = int(parts[-1])
                base_command = " ".join(parts[:-2])
                return self.schedule_command(base_command, delay_minutes, *parts[1:-2])

            # Handle regular commands
            command = " ".join(parts)  # Fixed: Join all parts to handle commands with spaces
            base_command = parts[0].lower()

            if command in self.command_map:
                self.command_map[command]()  # Fixed: Use full command string for lookup
            elif base_command in self.command_map:
                self.command_map[base_command](*parts[1:])
            elif base_command == 'sas' and len(parts) == 2:
                self.set_shutdown_time(parts[1])
            elif base_command == 'tas':
                self.toggle_auto_shutdown()
            elif base_command == 'sqa' and len(parts) == 2 and parts[1].isdigit():
                self.schedule_stop_all(int(parts[1]))
            elif base_command == 'wsqa' and len(parts) == 2 and parts[1].isdigit():
                self.warn_and_schedule_stop_all(int(parts[1]))
            elif base_command == 'rs' and len(parts) == 2:
                task_id = parts[1]
                if task_id in self.scheduled_tasks:
                    schedule.cancel_job(self.scheduled_tasks[task_id])
                    del self.scheduled_tasks[task_id]
                    print(f"Removed scheduled task: {task_id}")
                else:
                    print(f"No such scheduled task: {task_id}")
            elif base_command == 's' and len(parts) >= 2:
                message_body = " ".join(parts[1:])
                self.send_server_message(message_body)
            elif base_command == 'ss':
                self.show_scheduled_tasks()
            elif base_command == 'help':
                self.help()
            elif base_command == 'exit':
                self.stop_schedule_thread()
                print("Exiting Minecraft Server Manager.")
                sys.exit()
            else:
                print("Unknown command. Type 'help' for a list of commands.")
                return False

            return True

        except Exception as e:
            print(f"Error handling command: {e}")
            self.logger.log(f"Error handling command {command_input}: {e}")
            return False

    def help(self):
        """Display help information about commands."""
        help_text = """
Minecraft Server Manager Commands:
- sa           : Start server and Playit
- qa           : Stop server and Playit
- ra           : Restart server and Playit
- smc          : Start server
- qmc          : Stop server
- rmc          : Restart server
- st           : Start Playit
- qt           : Stop Playit
- rt           : Restart Playit
- backup       : Create world backup
- backup -m    : Create world milestone backup
- load         : Load latest backup
- load -m      : Load latest milestone backup
- log          : Show latest server log
- auto         : Toggle autobackup
- auto -m      : Toggle milestone backup
- sas <time>   : Set the auto-shutdown time (HH:MM)
- tas          : Toggle the auto-shutdown setting
- sqa <minutes>: Schedule server stop after a delay
- wsqa <minutes>: Warn players and schedule stop after a delay
- rs <task_id> : Remove a scheduled task by ID
- ss           : Show scheduled tasks
- s <txt>      : Send a message to console (/say is added) 
                 or a command (if it's already starting with /)
                 
Add -s <minutes> to any command to schedule it
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

    # Check if auto-shutdown is enabled in config and schedule it if necessary
    if manager.config_manager.is_auto_shutdown_enabled():
        manager._schedule_auto_shutdown()
        print(f"Auto-shutdown enabled at {manager.config_manager.get_auto_shutdown_time()}")

    print("Minecraft Server Manager")
    manager.help()

    while True:
        try:
            command_input = input("Enter command (or 'help' for options): ").strip()
            manager.handle_command(command_input)

        except Exception as e:
            print(f"An error occurred: {e}")
            manager.logger.log(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()