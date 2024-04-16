import datetime
from enum import Enum

class LogLevel(Enum):
    DEBUG = "debug"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

class Logger:
    def __init__(self):
        pass

    def log(self, message, level=LogLevel.INFO):
        if not isinstance(level, LogLevel):
            raise ValueError("Invalid log level")

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{current_time}] [{level.value.upper()}] {message}"
        print(log_message)
