from fastapi import APIRouter

router = APIRouter()


@router.get("/orders")
def list_orders():
    return repo.list()


@router.put("/orders/{order_id}")
def update_order(order_id: int, body: OrderIn):
    return repo.update(order_id, body)
