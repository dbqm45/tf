from fastapi import APIRouter, Depends

router = APIRouter()


@router.put("/orders/{order_id}")
def update_order(order_id: int, body: OrderIn, user=Depends(get_current_user)):
    return repo.update(order_id, body, user)
