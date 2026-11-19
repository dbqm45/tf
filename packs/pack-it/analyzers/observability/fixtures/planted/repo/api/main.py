import logging

from fastapi import FastAPI

log = logging.getLogger(__name__)
app = FastAPI()


@app.post("/payments")
def pay(amount: int):
    print("paying", amount)
    log.info("payment accepted")
    return {"ok": True}
