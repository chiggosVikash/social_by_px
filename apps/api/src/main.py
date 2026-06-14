from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from core.firebase import init_firebase

from api import projects, social_accounts, approvals

settings = get_settings()
init_firebase()  # [SOLID: DIP] — explicit initialization, not import side-effect

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for AI News-to-Carousel Automation Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL], # Restricted to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter
from api import projects, social_accounts, approvals, websockets

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(projects.router)
api_router.include_router(social_accounts.router)
api_router.include_router(approvals.router)
api_router.include_router(websockets.router, prefix="/ws")

from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
