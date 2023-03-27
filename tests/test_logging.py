from spelunk.logging import get_logger
from logging import NOTSET, DEBUG, WARNING, ERROR, CRITICAL, StreamHandler
import pytest


@pytest.mark.parametrize("level", [NOTSET, DEBUG, WARNING, ERROR, CRITICAL])
def test_get_logger(level: int) -> None:
    logger = get_logger(name="unique_name", level=level)
    assert logger.name == "unique_name"
    assert not logger.propagate
    assert logger.level == level
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], StreamHandler)
