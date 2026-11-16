import logging

log = logging.getLogger(__name__)


def zaplac(kwota):
    log.info("płacę %s", kwota)
    return kwota
