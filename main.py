from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import engine, Base
from app.websocket_manager import manager
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle"""
    logger.info("Starting ZZLWR BlackCipher Trader Backend")
    yield
    logger.info("Shutting down ZZLWR BlackCipher Trader Backend")


# Initialize FastAPI app
app = FastAPI(
    title="ZZLWR BlackCipher Trader API",
    description="AI-Powered Automated Trading Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ZZLWR BlackCipher Trader",
        "version": "1.0.0"
    }


# WebSocket endpoint for real-time trading data
@app.websocket("/ws/trading/{user_id}/{token}")
async def websocket_trading_endpoint(websocket: WebSocket, user_id: int, token: str):
    """
    WebSocket endpoint for real-time trading updates
    Streams: price updates, signals, trade fills, risk alerts
    """
    await websocket.accept()
    await manager.connect(websocket, f"user_{user_id}")
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Receive heartbeat or commands from client
            data = await websocket.receive_text()
            
            # Parse incoming message
            try:
                message = json.loads(data)
                message_type = message.get("type", "ping")
                
                if message_type == "ping":
                    # Send pong response
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message_type == "subscribe":
                    # Subscribe to specific data streams
                    symbols = message.get("symbols", [])
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "symbols": symbols,
                        "timestamp": datetime.now().isoformat()
                    })
                elif message_type == "unsubscribe":
                    symbols = message.get("symbols", [])
                    await websocket.send_json({
                        "type": "unsubscription_confirmed",
                        "symbols": symbols,
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(f"user_{user_id}")
        logger.info(f"User {user_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(f"user_{user_id}")


# Import route modules
from app.api import auth, trades, signals, market, broker, portfolio, risk

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(broker.router, prefix="/api/broker", tags=["broker"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
