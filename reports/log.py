import logging
from logging.config import fileConfig, dictConfig
from ExtendedJournalHandler import ExtendedJournalHandler

SYS_LOG = {
    "SYSLOG_IDENTIFIER": "API_BILLING",
    "level": logging.INFO
}

def getLogger(name):
    logger = logging.getLogger(name)
    handler = ExtendedJournalHandler(**SYS_LOG)
    handler.setFormatter(logger.root.handlers[0].formatter)
    logger.addHandler(handler)
    return logger
