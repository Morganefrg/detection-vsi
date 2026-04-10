import numpy as np
from collections import deque

def compute_features(history: deque) -> dict | None:
    """
    Calcule les features comportementales depuis l'historique
    des positions d'une personne.
    
    history: deque de tuples (cx, cy, timestamp)
    Retourne un dictionnaire avec les 4 features, ou None si
    pas assez de données.
    """
    # Il faut au moins 10 positions pour calculer les features
    if len(history) < 10:
        return None

    positions = list(history)
    
    # Durée totale en secondes
    duration = positions[-1][2] - positions[0][2]
    if duration <= 0:
        return None

    # Calcul des distances entre positions successives
    distances = []
    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i-1][0]
        dy = positions[i][1] - positions[i-1][1]
        distances.append(np.sqrt(dx**2 + dy**2))

    # Feature 1 — vitesse moyenne (pixels/seconde)
    total_distance = sum(distances)
    avg_speed = total_distance / duration

    # Feature 2 — changements de direction par seconde
    direction_changes = 0
    for i in range(1, len(distances)):
        if abs(distances[i] - distances[i-1]) > 2:
            direction_changes += 1
    direction_changes_per_sec = direction_changes / duration

    # Feature 3 — ratio du temps passé immobile
    stopped_frames = sum(1 for d in distances if d < 2)
    stopped_ratio = stopped_frames / len(distances)

    # Feature 4 — distance totale parcourue
    return {
        "avg_speed": avg_speed,
        "direction_changes_per_sec": direction_changes_per_sec,
        "stopped_ratio": stopped_ratio,
        "total_distance": total_distance
    }