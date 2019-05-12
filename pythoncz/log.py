import os
import logging


level = getattr(logging, os.getenv('LOG_LEVEL', 'WARNING').upper())
logging.basicConfig(format='%(name)s - %(levelname)s: %(message)s',
                    level=level)


def get(name):
    logger = logging.getLogger(name)
    logger.setLevel(level=logging.INFO)
    return logger
