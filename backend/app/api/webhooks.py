from fastapi import APIRouter, status

router = APIRouter(prefix="/webhooks")


@router.post("/gmail", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_webhook():
    pass
