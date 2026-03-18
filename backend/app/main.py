from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import brackets, games, notifications, scores, sync
from app.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(brackets.router, prefix="/api/v1", tags=["brackets"])
app.include_router(games.router, prefix="/api/v1", tags=["games"])
app.include_router(scores.router, prefix="/api/v1", tags=["scores"])
app.include_router(sync.router, prefix="/api/v1", tags=["sync"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "NCAA Bracket Tracker API", "version": "0.1.0"}
