from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import games, streams, users
from app.core.config import settings

app = FastAPI(
    title="NBA Commentary API",
    description="Real-time NBA game commentary with text-to-speech",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games.router, prefix="/api/games", tags=["games"])
app.include_router(streams.router, prefix="/api/streams", tags=["streams"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to NBA Commentary API"} 