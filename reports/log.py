import logging
from ExtendedJournalHandler import ExtendedJournalHandler


SYS_LOG = {
    "SYSLOG_IDENTIFIER": "API_BILLING",
    "level": logging.INFO
}


def getLogger(name):
    logger = logging.getLogger(name)
    handler = ExtendedJournalHandler(**SYS_LOG)
    if logger.root.handlers:
        handler.setFormatter(logger.root.handlers[0].formatter)
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)-8s %(message)s")
        )
    logger.addHandler(handler)
    return logger
