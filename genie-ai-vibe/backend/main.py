import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.agent_routes import router as agent_router
from api.device_routes import router as device_router
from api.mood_routes import router as mood_router
from api.face_routes import router as face_router
from api.proactive_routes import router as proactive_router
from db.db_handler import init_db
import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Genie AI Backend...")
    init_db()
    print("Database initialized successfully")
    yield
    # Shutdown
    print("Shutting down Genie AI Backend...")

app = FastAPI(
    title="Genie AI Smart Home Backend", 
    version="2.0.0",
    description="AI-powered smart home assistant with device control and mood management",
    lifespan=lifespan
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(agent_router, prefix="/api", tags=["AI Agent"])
app.include_router(device_router, prefix="/api", tags=["Devices"])
app.include_router(mood_router, prefix="/api", tags=["Mood & Themes"])
app.include_router(face_router, prefix="/api", tags=["Face Recognition"])
app.include_router(proactive_router, prefix="/api", tags=["Proactive Intelligence"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Genie AI Smart Home Backend Running!",
        "version": "2.0.0",
        "features": ["AI Chat", "Device Control", "Mood Management", "Scene Control", "Face Recognition", "Smart Doorbell", "Proactive Intelligence", "Weather-based Automation", "Behavioral Learning"]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "genie-ai-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT) 