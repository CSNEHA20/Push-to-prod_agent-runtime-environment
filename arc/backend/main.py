import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("arc.backend")

# Active WebSocket connections registry
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

ws_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown procedures."""
    logger.info("Initializing Agent Runtime Core (ARC) Backend...")
    # Startup tasks: db initialization, redis connection pool initialization
    yield
    # Shutdown tasks: closing pools, cleanup connections
    logger.info("Shutting down Agent Runtime Core (ARC) Backend...")

app = FastAPI(
    title="Agent Runtime Core (ARC) API",
    description="Reliability layer for Claude AI agents featuring Flight Recorder, Context Firewall, and Recovery Engine.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from api.routes.sessions import router as sessions_router
    from api.routes.traces import router as traces_router
    from api.routes.context import router as context_router
    from api.websocket import router as ws_router
except ImportError:
    from arc.backend.api.routes.sessions import router as sessions_router
    from arc.backend.api.routes.traces import router as traces_router
    from arc.backend.api.routes.context import router as context_router
    from arc.backend.api.websocket import router as ws_router

app.include_router(sessions_router)
app.include_router(traces_router)
app.include_router(context_router)
app.include_router(ws_router)

@app.get("/")
async def root_route() -> Dict[str, Any]:
    """Root endpoint returning service status."""
    return {
        "service": "Agent Runtime Core (ARC)",
        "status": "online",
        "engines": {
            "flight_recorder": "active",
            "context_firewall": "active",
            "recovery_engine": "active"
        },
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Production health check endpoint."""
    return {
        "status": "healthy",
        "service": "ARC Engine",
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "flight_recorder": "operational",
            "context_firewall": "operational",
            "recovery_engine": "operational"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Live WebSocket stream endpoint for ARC flight recorder traces."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process incoming commands from frontend/sdk clients
            await websocket.send_json({"type": "ack", "message": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
