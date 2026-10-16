import json
import logging
import secrets
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    status,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.schemas_bak import PubSubEnvelope

from .core.config import Settings, settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from googleapiclient.errors import HttpError
from app.utils.Gmail import gmail

logger = logging.getLogger(__name__)


def verify_pubsub_oidc_token(req: Request) -> bool:
    """Xác minh OIDC Token do Pub/Sub gửi kèm trong Header"""
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False

    token = auth_header.split("Bearer ")[1]

    try:
        claim = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=settings.pubsub_oidc_audience,
        )
        # Kiểm tra email service account phát hành token
        expected_email = settings.pubsub_service_account_email
        if not expected_email or claim.get("email") != expected_email:
            print(expected_email, claim.get("email"))
            return False
        return True
    except Exception as e:

        return False


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Khởi động Gmail watch
    try:
        result = gmail.watch_email()
        print(f"Gmail watch started: {result}")
    except Exception as e:
        print(f"Failed to start Gmail watch: {e}")
    yield


app = FastAPI(lifespan=lifespan, root_path="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to logs for tracing."""
    request_id = secrets.token_hex(8)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


_sync_lock = Lock()


def run_sync_history_safe(settings: Settings, history_id: str) -> None:
    if not _sync_lock.acquire(blocking=False):
        logger.info(f"Đã có tiến trình sync đang chạy. Bỏ qua history_id {history_id}")
        return

    db = next(get_db())
    try:
        sync_history(db, settings, history_id)
    except HttpError as error:
        if error.resp.status == 403 and "rateLimitExceeded" in str(error):
            logger.warning("Chạm hạn ngạch Gmail API, sẽ tự hồi phục ở đợt sync sau.")
        else:
            logger.error(f"Lỗi Gmail API khi sync {history_id}: {error}", exc_info=True)
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi sync {history_id}: {e}", exc_info=True)
    finally:
        db.close()
        _sync_lock.release()


@app.post("/api/webhooks/gmail", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_webhook(
    req: Request,
    envelope: PubSubEnvelope,
    background_tasks: BackgroundTasks,
) -> None:
    # Xác thực OIDC token từ Pub/Sub
    if settings.pubsub_oidc_audience:
        if not verify_pubsub_oidc_token(req):
            raise HTTPException(status_code=401, detail="Invalid OIDC token")

    try:
        notification = decode_pubsub_data(envelope.message.data)
        history_id = notification["historyId"]

        background_tasks.add_task(run_sync_history_safe, settings, history_id)

    except (KeyError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=400, detail="Invalid Gmail notification"
        ) from error


from app.api import auth, absentRequests

app.include_router(router=auth.router)
app.include_router(router=absentRequests.router)

app.mount("/", StaticFiles(directory="../frontend/dist"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
