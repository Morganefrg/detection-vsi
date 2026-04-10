import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from db.connection import get_connection
from typing import List
import json

app = FastAPI(title="VSI - Vidéo Surveillance Intelligente")

# Configuration CORS — permet au frontend React de parler à l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Envoie un message à tous les clients connectés"""
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/")
def root():
    return {"message": "VSI API en ligne ✅"}

@app.get("/violations")
def get_violations():
    """Retourne l'historique des violations"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT v.id, v.type, v.timestamp,
                       t.track_id, t.object_type
                FROM violation v
                JOIN tracked_object t ON v.object_id = t.id
                ORDER BY v.timestamp DESC
                LIMIT 50
            """)
            rows = cursor.fetchall()
    return {"violations": rows}

@app.get("/stats")
def get_stats():
    """Retourne les statistiques globales"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM tracked_object")
            total_objects = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM violation")
            total_violations = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM violation
                GROUP BY type
            """)
            by_type = cursor.fetchall()

    return {
        "total_objects": total_objects,
        "total_violations": total_violations,
        "by_type": by_type
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour les violations en temps réel"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)