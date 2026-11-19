from fastapi import APIRouter, Depends

router = APIRouter(dependencies=[Depends(require_admin)])


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    return repo.delete(user_id)
