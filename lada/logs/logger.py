from pathlib import Path
from datetime import datetime
from lada.logging.loader import LoggingLoader

class Logger:
    def __init__(self,path="lada/logs"):
        self.path=Path(path)
        self.path.mkdir(
            parents=True,
            exist_ok=True
        )
        self.loader=LoggingLoader()
    def write(
        self,
        filename,
        message,
        user_id=None
    ):
        logfile=self.path/f"{filename}.log"
        prompt=self.loader.get(filename)
        with open(
            logfile,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(
                "\n"
                "============================================================\n"
            )
            file.write(
                f"TIME: {datetime.now().isoformat(timespec='seconds')}\n"
            )
            if user_id:
                file.write(
                    f"USER: {user_id}\n"
                )
            file.write(
                f"TYPE: {filename}\n\n"
            )
            if prompt:
                file.write(
                    "[LOGGING RULES]\n"
                )
                file.write(prompt)
                file.write("\n\n")
            file.write(
                "[MESSAGE]\n"
            )
            file.write(message)
            file.write("\n")
    def brain(
        self,
        message,
        user_id=None
    ):
        self.write(
            "brain",
            message,
            user_id
        )
    def memory(
        self,
        message,
        user_id=None
    ):
        self.write(
            "memory",
            message,
            user_id
        )
    def chat(
        self,
        message,
        user_id=None
    ):
        self.write(
            "chat",
            message,
            user_id
        )
    def system(
        self,
        message,
        user_id=None
    ):
        self.write(
            "system",
            message,
            user_id
        )
    def error(
        self,
        message,
        user_id=None
    ):
        self.write(
            "error",
            message,
            user_id
        )