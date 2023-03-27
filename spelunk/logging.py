"""Module containing logging setup function."""
from typing import Optional, Union
from logging import getLogger, INFO, StreamHandler, Logger


def get_logger(name: Optional[str] = None, level: Union[str, int] = INFO) -> Logger:
    """Get a new logger instance and set it up to use a single console handler."""
    logger = getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    streamHandler = StreamHandler()
    streamHandler.setLevel(level)
    logger.handlers = [streamHandler]
    return logger
