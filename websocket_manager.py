from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # client_id -> list of subscriptions

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = []
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def broadcast(self, message: str):
        """Send message to all connected clients"""
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")

    async def broadcast_to_subscribed(self, channel: str, message: dict):
        """Send message only to clients subscribed to channel"""
        for client_id, subscriptions in self.subscriptions.items():
            if channel in subscriptions and client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {client_id}: {str(e)}")

    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending personal message to {client_id}: {str(e)}")

    def subscribe(self, client_id: str, channel: str):
        """Subscribe client to a channel"""
        if client_id in self.subscriptions:
            if channel not in self.subscriptions[client_id]:
                self.subscriptions[client_id].append(channel)
                logger.info(f"Client {client_id} subscribed to {channel}")

    def unsubscribe(self, client_id: str, channel: str):
        """Unsubscribe client from a channel"""
        if client_id in self.subscriptions:
            if channel in self.subscriptions[client_id]:
                self.subscriptions[client_id].remove(channel)
                logger.info(f"Client {client_id} unsubscribed from {channel}")

    def get_connected_clients_count(self) -> int:
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()
