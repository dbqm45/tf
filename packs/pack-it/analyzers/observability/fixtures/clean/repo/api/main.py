import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

log = logging.getLogger(__name__)
app = FastAPI()
app.add_middleware(CorrelationIdMiddleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/payments")
def pay(amount: int):
    log.info("payment accepted", extra={"amount": amount})
    try:
        return {"ok": True}
    except FileNotFoundError:
        pass  # brak pliku to stan normalny


def parse(raw):
    import json
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    return None
