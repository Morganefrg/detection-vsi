import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from db.connection import get_connection
from datetime import datetime
from typing import List

app = FastAPI(title="VSI - Vidéo Surveillance Intelligente")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

async def notify_violation(violation_type: str, track_id: int):
    """
    Envoie une nouvelle violation à tous les clients WebSocket connectés.
    """
    await manager.broadcast({
        "type": "violation",
        "violation": {
            "type": violation_type,
            "track_id": track_id,
            "timestamp": str(datetime.now())
        }
    })

# Connecte le callback du repository au WebSocket
import db.repository as repo
repo.on_violation_callback = notify_violation

@app.get("/")
def root():
    return {"message": "VSI API en ligne ✅"}

@app.get("/violations")
def get_violations():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT v.id, v.type, v.zone, v.timestamp,
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

@app.delete("/reset")
def reset_database():
    """
    Vide la base de données — à utiliser avant chaque démo.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM violation")
            cursor.execute("DELETE FROM tracked_object")
            conn.commit()
    return {"message": "Base de données réinitialisée ✅"}



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)