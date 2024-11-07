import os
import subprocess
import sys
from typing import Optional
import pwd
import grp


def get_non_privileged_user() -> str:
    """
    Find a non-privileged user account on the system.

    :return: Username of a non-privileged user.
    """
    for user in pwd.getpwall():
        if 1000 <= user.pw_uid < 65534:
            return user.pw_name

    raise ValueError("No non-privileged user found on the system")


def run_script(scripts_dir: str, script_name: str, logger, log_message: Optional[str] = None) -> bool:
    """
    Run a script from the scripts directory as a non-privileged user.

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

        # Find a non-privileged user account
        non_privileged_user = get_non_privileged_user()
        non_privileged_uid = pwd.getpwnam(non_privileged_user).pw_uid
        non_privileged_gid = grp.getgrnam(non_privileged_user).gr_gid

        # Run the script using the non-privileged user's environment
        result = subprocess.run([sys.executable, script_path],
                                capture_output=True,
                                text=True,
                                check=True,
                                preexec_fn=lambda: os.setgid(non_privileged_gid) or os.setuid(non_privileged_uid))

        # Print script output
        if result.stdout:
            print(result.stdout)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        logger.log(f"Error running {script_name}: {e}")
        return False