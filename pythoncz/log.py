import logging


logging.basicConfig(format='%(name)s - %(levelname)s: %(message)s')


def get(name):
    logger = logging.getLogger(name)
    logger.setLevel(level=logging.INFO)
    return logger
