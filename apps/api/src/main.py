from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings

from api import projects, social_accounts

settings = get_settings()

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

app.include_router(projects.router)
app.include_router(social_accounts.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
