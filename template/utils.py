import logging
import os
import sys
from typing import Optional

import structlog
from structlog.stdlib import BoundLogger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT = os.getenv("LOG_FORMAT", "JSON")
log: Optional[BoundLogger] = None


def absolute_path(path: str) -> str:
    """Makes a path which is relative to the root dir become absolute."""
    return os.path.join(ROOT_DIR, path)


def add_locals_to_log(_, __, event_dict):
    if "exc_info" in event_dict:
        exc_type, exc_value, exc_traceback = event_dict["exc_info"]
        stack = exc_traceback.tb_frame
        event_dict["locals"] = stack.f_locals
    return event_dict


def get_logger() -> BoundLogger:
    global log
    if log:
        return log

    logging.basicConfig(stream=sys.stdout, format="%(message)s")

    log_renderer = (
        structlog.dev.ConsoleRenderer
        if LOG_FORMAT == "CONSOLE"
        else structlog.processors.JSONRenderer
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_locals_to_log,
            log_renderer(),
        ],
        wrapper_class=BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log = structlog.get_logger()
    log.setLevel(LOG_LEVEL)

    # write logs to file as well as stdout
    file_handler = logging.FileHandler(absolute_path("logs.log"), mode="a")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(file_handler)

    return log
