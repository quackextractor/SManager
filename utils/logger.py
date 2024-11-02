# utils/logger.py
import datetime
import os


class Logger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    def log(self, message):
        """
        Log a message with timestamp to file and print to console
        
        :param message: Message to log
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # Print to console
        print(log_entry)

        # Write to log file
        try:
            with open(self.log_file_path, 'a') as log_file:
                log_file.write(log_entry + '\n')
        except IOError as e:
            print(f"Error writing to log file: {e}")
