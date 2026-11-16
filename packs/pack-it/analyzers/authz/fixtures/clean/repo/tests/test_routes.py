from fastapi import APIRouter

router = APIRouter()


@router.post("/fake")
def fake():
    return 1
