import logging

log = logging.getLogger(__name__)


def send_sms(phone: str, text: str) -> None:
    log.info("sending sms to %s", phone)
