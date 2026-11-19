import logging

log = logging.getLogger(__name__)


def pay(amount):
    log.info("paying %s", amount)
    return amount
