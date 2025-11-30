import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import (
    base_router,
    book_router,
    book_page_router,
    auth_router,
    user_router,
    review_router,
    progress_router,
    admin_book_router,
    admin_user_router,
    admin_review_router,
    admin_analytics_router,
    admin_csv_router
)
from helpers.config import settings

app = FastAPI(
    title="BookLook API",
    description="Enhanced book library application with reading progress tracking",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (root level for Docker healthcheck)
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "service": "booklook-backend"}

# Register routers
app.include_router(base_router)
app.include_router(book_router, prefix="/api/v1")
app.include_router(book_page_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")

# Register admin routers
app.include_router(admin_book_router, prefix="/api/v1")
app.include_router(admin_user_router, prefix="/api/v1")
app.include_router(admin_review_router, prefix="/api/v1")
app.include_router(admin_analytics_router, prefix="/api/v1")
app.include_router(admin_csv_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
