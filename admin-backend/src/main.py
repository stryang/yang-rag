"""Yang RAG Admin - FastAPI Backend Application."""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db
from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.knowledge.router import router as knowledge_router
from src.runtime_settings.router import router as runtime_settings_router
from src.system.router import router as system_router
from src.vector_databases.router import router as vector_databases_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    Path("./data").mkdir(exist_ok=True)
    await init_db()

    # Create default admin user if not exists
    from src.database import async_session_maker
    from src.models import User
    from sqlalchemy import select
    from src.auth.utils import get_password_hash

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("Default admin user created: admin / admin123")

    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Yang RAG Admin API",
    description="Backend API for Yang RAG Admin Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(knowledge_router)
app.include_router(runtime_settings_router)
app.include_router(system_router)
app.include_router(vector_databases_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Yang RAG Admin API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
