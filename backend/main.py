from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import STORAGE_PATH, STORAGE_PROVIDER
from backend.models.job import init_db
from backend.routes import clip, status

app = FastAPI(title="Clipper AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


STORAGE_PATH.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(clip.router, prefix="/api")
app.include_router(status.router, prefix="/api")

if STORAGE_PROVIDER == "local":
    app.mount("/clips", StaticFiles(directory=str(STORAGE_PATH)), name="clips")


@app.get("/health")
def health():
    return {"status": "ok"}
