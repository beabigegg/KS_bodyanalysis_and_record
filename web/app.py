from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from routes.compare import router as compare_router
from routes.imports import router as imports_router
from routes.r2r import router as r2r_router
from routes.trend import router as trend_router
from routes.yield_corr import router as yield_router
from config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="KS Recipe Analysis WebUI",
    version="0.1.0",
    debug=settings.debug,
)

# CORS — 禁止 "*", 使用 .env 明確清單
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 統一錯誤處理 middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(imports_router)
app.include_router(compare_router)
app.include_router(trend_router)
app.include_router(r2r_router)
app.include_router(yield_router)


@app.get("/api/health", response_model=None)
def health():
    return {"data": "ok", "total": 1}


# 靜態檔案託管 — 單體式架構，前端由後端統一伺服
FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", response_model=None)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        target = (FRONTEND_DIST / full_path).resolve()
        if full_path and target.is_relative_to(FRONTEND_DIST) and target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    log_level = "debug" if settings.debug else "info"
    uvicorn.run(
        "app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_mode == "dev"),
        log_level=log_level,
    )
