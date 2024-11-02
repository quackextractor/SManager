# utils/run_script.py
import os
import subprocess
from typing import Optional


def run_script(scripts_dir: str, script_name: str, logger, log_message: Optional[str] = None) -> bool:
    """
    Run a script from the scripts directory.

    :param scripts_dir: Directory where scripts are located.
    :param script_name: Name of the script to run.
    :param logger: Logger instance for logging actions.
    :param log_message: Optional log message to write.
    :return: True if script ran successfully, False otherwise.
    """
    try:
        script_path = os.path.join(scripts_dir, script_name)

        # Log the action
        if log_message:
            logger.log(log_message)

        # Run the script
        result = subprocess.run(['python3', script_path],
                                capture_output=True,
                                text=True,
                                check=True)

        # Print script output
        if result.stdout:
            print(result.stdout)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        logger.log(f"Error running {script_name}: {e}")
        return False
