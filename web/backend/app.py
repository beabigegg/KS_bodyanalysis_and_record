from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.compare import router as compare_router
from api.imports import router as imports_router
from api.r2r import router as r2r_router
from api.trend import router as trend_router
from api.yield_corr import router as yield_router
from config import settings

app = FastAPI(title="KS Recipe Analysis Web Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(imports_router)
app.include_router(compare_router)
app.include_router(trend_router)
app.include_router(r2r_router)
app.include_router(yield_router)


@app.get("/api/health", response_model=None)
def health():
    return {"data": "ok", "total": 1}


FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
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
