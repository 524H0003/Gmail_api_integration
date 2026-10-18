from pathlib import Path
import secrets
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn


from app.utils.Gmail import gmail



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


from app.api import auth, absentRequests, webhooks

app.include_router(router=auth.router)
app.include_router(router=absentRequests.router)
app.include_router(router=webhooks.router)

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR.parent.parent / "frontend" / "dist"

if DIST_DIR.exists():
    # Handlers phục vụ Single Page Application (React/Vite)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(DIST_DIR / "index.html")

else:
    print(f"CẢNH BÁO: Thư mục frontend không tồn tại tại {DIST_DIR}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
