from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ksbody.web.routes.compare import router as compare_router
from ksbody.web.routes.imports import router as imports_router
from ksbody.web.routes.r2r import router as r2r_router
from ksbody.web.routes.trend import router as trend_router
from ksbody.web.routes.watcher import router as watcher_router
from ksbody.web.routes.yield_corr import router as yield_router
from ksbody.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="KS Recipe Analysis WebUI",
    version="0.1.0",
    debug=settings.debug,
)

# CORS ??禁止 "*", 使用 .env ?�確清單
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 統�??�誤?��? middleware
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
app.include_router(watcher_router)
app.include_router(yield_router)


@app.get("/api/health", response_model=None)
def health():
    return {"data": "ok", "total": 1}


# ?��?檔�?託管 ???��?式架構�??�端?��?端統一伺�?
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
        "ksbody.web.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_mode == "dev"),
        log_level=log_level,
    )
