import os
import logging
import sys


class Log:
    _logger = None  # Shared logger instance

    @classmethod
    def get_logger(cls, filename):
        """
        Initialize and return a logger object.

        Args:
            filename (str): The name of the log file.

        Returns:
            logging.Logger: The logger object.

        """
        if cls._logger is None:
            cls._logger = cls._setup_logger(filename)
        else:
            logging.info("Logger already initialized.")
        return cls._logger

    @classmethod
    def _setup_logger(cls, filename):
        """
        Set up the logger object with the specified filename.

        Returns:
            logging.Logger: The logger object.

        """
        formatter = logging.Formatter('%(levelname)s-%(asctime)s-%(message)s')
        logger = logging.getLogger(filename)
        logger.setLevel(logging.DEBUG)

        logs_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        log_filename = os.path.join(logs_dir, f'{filename}.log')
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)


        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        # Add a stream handler to log to the terminal
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        return logger

    def info(self, message):
        """
        Log an informational message.

        Args:
            message (str): The message to be logged.

        """
        self.get_logger().info(message)

    def warning(self, message):
        """
        Log a warning message.

        Args:
            message (str): The message to be logged.

        """
        self.get_logger().warning(message)

    def error(self, message):
        """
        Log an error message.

        Args:
            message (str): The message to be logged.

        """
        self.get_logger().error(message)


# Usage example:
if __name__ == '__main__':
    my_logger = Log.get_logger('log')
    my_logger.info('Logging from the shared logger')
    my_logger.error('An error occurred in the shared logger')
