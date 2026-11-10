import logging


def test_log(caplog):
    email = "a@example.com"
    logging.info("user %s", email)
