"""
Socket.IO server manager for real-time WebSocket connections
"""
import logging
from typing import Set

import socketio

logger = logging.getLogger(__name__)

# Create Socket.IO async server with CORS support
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

# Track connected clients
connected_clients: Set[str] = set()


@sio.event
async def connect(sid: str, environ: dict):
    """Handle client connection"""
    connected_clients.add(sid)
    logger.info(f"WebSocket client connected: {sid} (total: {len(connected_clients)})")

    # Send connection confirmation
    await sio.emit('connection:status', {
        'status': 'connected',
        'client_id': sid,
        'total_clients': len(connected_clients)
    }, to=sid)


@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    connected_clients.discard(sid)
    logger.info(f"WebSocket client disconnected: {sid} (total: {len(connected_clients)})")


@sio.event
async def ping(sid: str, data: dict):
    """Handle ping from client"""
    await sio.emit('pong', {'timestamp': data.get('timestamp')}, to=sid)


async def broadcast_event(event: str, data: dict):
    """
    Broadcast event to all connected clients

    Args:
        event: Event name (e.g., 'feedback:new', 'feedback:completed')
        data: Event payload
    """
    if connected_clients:
        logger.info(f"Broadcasting '{event}' to {len(connected_clients)} clients")
        await sio.emit(event, data)
    else:
        logger.debug(f"No clients connected for event: {event}")


def get_connected_count() -> int:
    """Get number of connected clients"""
    return len(connected_clients)


# Create ASGI app - will be used to wrap FastAPI app
def create_socket_app(fastapi_app):
    """
    Create Socket.IO ASGI app wrapping FastAPI

    Args:
        fastapi_app: FastAPI application instance

    Returns:
        socketio.ASGIApp wrapping the FastAPI app
    """
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)


# Placeholder for the wrapped app (will be set in main.py)
socket_app = None
