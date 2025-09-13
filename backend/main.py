"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.api.routes.auth import router as auth_router
from src.application.api.routes.health import router as health_router
from src.application.api.routes.receipts import router as receipts_router
from src.application.api.routes.search import router as search_router

app = FastAPI(
    title="Receipt Search API",
    description="API for receipt management and search",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(receipts_router, prefix="/api/v1/receipts", tags=["receipts"])
app.include_router(search_router, prefix="/api/v1/search", tags=["search"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Receipt Search API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
