import logging
import socket
from logging.handlers import SysLogHandler

from local import *


syslog = SysLogHandler(address=(REMOTE_LOGGING_URL, REMOTE_LOGGING_PORT))
logFormat = "%(asctime)s {}: %(message)s ".format(APP_NAME)
formatter = logging.Formatter(logFormat, datefmt = "%b %d %H:%M:%S")

syslog.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)


def logInfo(msg):

    logger.info(msg)


def logWarning(msg):

    logger.warning(msg)

def logError(e):

    logger.error(e)

def logException(e):
    logger.exception(e)
