from datetime import datetime
from db.connection import get_connection

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

def insert_violation(track_id: int, violation_type: str) -> None:
    """
    Enregistre une violation pour un objet tracké.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # On récupère l'id de l'objet
            cursor.execute(
                "SELECT id FROM tracked_object WHERE track_id = %s",
                (track_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return
            # On insère la violation
            cursor.execute("""
                INSERT INTO violation (object_id, type, timestamp)
                VALUES (%s, %s, %s)
            """, (result["id"], violation_type, datetime.now()))
            conn.commit()