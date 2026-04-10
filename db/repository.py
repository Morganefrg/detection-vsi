from datetime import datetime
from db.connection import get_connection

# Callback optionnel — sera défini par l'API pour notifier le WebSocket
on_violation_callback = None

def insert_tracked_object(track_id: int, object_type: str) -> int:
    """
    Insère un objet tracké s'il n'existe pas déjà.
    Retourne l'id de l'objet dans la base de données.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tracked_object (track_id, object_type, first_seen, last_seen)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (track_id) DO UPDATE
                SET last_seen = EXCLUDED.last_seen
                RETURNING id
            """, (track_id, object_type, datetime.now(), datetime.now()))
            conn.commit()
            return cursor.fetchone()["id"]

def insert_violation(track_id: int, violation_type: str, zone: str = None) -> None:
    """
    Enregistre une violation pour un objet tracké.
    Notifie le WebSocket si un callback est défini.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM tracked_object WHERE track_id = %s",
                (track_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return
            cursor.execute("""
                INSERT INTO violation (object_id, type, zone, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (result["id"], violation_type, zone, datetime.now()))
            conn.commit()

    # Notifie le WebSocket si callback défini
    if on_violation_callback:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(on_violation_callback(violation_type, track_id))
            else:
                loop.run_until_complete(on_violation_callback(violation_type, track_id))
        except Exception as e:
            print(f"WebSocket notification error: {e}")