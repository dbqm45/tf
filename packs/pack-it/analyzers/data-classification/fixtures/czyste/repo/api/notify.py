import logging

log = logging.getLogger(__name__)


def send_sms(phone: str, text: str) -> None:
    log.info("sending sms, phone number masked")
    print(f"sms queued: {len(text)} chars")


def report(row: dict) -> None:
    print(f"{row['id']} {'' if row.get('checked') else ' · adres niesprawdzony'}")
