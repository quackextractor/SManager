import subprocess
import time
import os

# Get the base directory of the script (where `schedule_shutdown.py` is located)
base_dir = os.path.dirname(os.path.abspath(__file__))

def send_warning(message: str):
    """Send a server warning message."""
    # Construct the relative path for message.py
    message_script = os.path.join(base_dir, '..', 'utils', 'message.py')
    subprocess.run(['/usr/bin/python3', message_script, message])

def main():
    # 30 minute warning
    send_warning("Server shutdown in 30 minutes!")

    # Wait 20 minutes (to make it 10 minutes before shutdown)
    time.sleep(1200)

    # 10 minute warning
    send_warning("Server shutdown in 10 minutes!")

    # Wait 9 minutes (to make it 1 minute before shutdown)
    time.sleep(540)

    # 1 minute warning
    send_warning("Server shutdown in 1 minute!")

    # Wait 50 seconds (to make it 10 seconds before shutdown)
    time.sleep(50)

    # 10 second countdown warning
    send_warning("Server shutting down in 10 seconds!")

    # Execute the shutdown command
    stop_script = os.path.join(base_dir, '..', 'scripts', 'stop_mc.py')
    subprocess.run(['/usr/bin/python3', stop_script])

if __name__ == "__main__":
    main()
