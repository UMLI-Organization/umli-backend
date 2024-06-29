from typing import IO
import logging

from umli_backend.settings import LOGGING


main_logger_name = next(iter(LOGGING['loggers'].keys()))
logger = logging.getLogger(main_logger_name).getChild(__name__)


def decode_file(file: IO, encoding: str = 'utf-8') -> str:
    try:
        return file.read().decode(encoding)
    except UnicodeDecodeError as ex:
        logger.error(f"Error decoding file: {file} with encoding: {encoding}.\nError: {ex}")