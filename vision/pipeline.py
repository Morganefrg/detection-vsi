import cv2
import time
import yaml
import numpy as np
import joblib
from collections import defaultdict, deque
from ultralytics import YOLO

from vision.utils.capture import get_video_source
from vision.utils.geometry import point_in_zone, get_foot_point, is_fallen
from vision.utils.features import compute_features
from db.repository import insert_tracked_object, insert_violation

def load_zones(yaml_path: str) -> list:
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return data["zones"]

violation_memory = defaultdict(dict)

def draw_alert(frame, message: str, color: tuple, position: int):
    """
    Affiche un message d'alerte sur la frame vidéo.
    position: numéro de ligne (0, 1, 2...) pour empiler les alertes
    """
    y = 30 + position * 35
    cv2.rectangle(frame, (0, y - 20), (400, y + 10), (0, 0, 0), -1)
    cv2.putText(frame, message, (10, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def run_pipeline(source: str, model_path: str, zones_path: str,
                 anomaly_model_path: str = "data/anomaly_model.pkl"):
    model = YOLO(model_path)
    zones = load_zones(zones_path)
    anomaly_model = joblib.load(anomaly_model_path)
    print(f"✅ Modèle anomalie chargé")

    track_history = defaultdict(lambda: deque(maxlen=150))
    zone_frame_counter = defaultdict(lambda: defaultdict(int))
    # Alertes persistantes — restent affichées 3 secondes
    persistent_alerts = []

    cap = get_video_source(source)
    if not cap.isOpened():
        print("Erreur : impossible d'ouvrir la source vidéo")
        return

    print("Pipeline démarré. Appuie sur 'q' pour quitter.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            frame,
            persist=True,
            classes=[0],
            conf=0.25,
            vid_stride=2,
            imgsz=320
        )

        # Liste des alertes à afficher sur la frame
        alerts = []

        if results[0].boxes.id is None:
            cv2.imshow("VSI - Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)

        for bbox, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = bbox
            cx = int((x1 + x2) / 2)
            cy = int(y2)
            now = time.time()

            track_history[track_id].append((cx, cy, now))
            insert_tracked_object(int(track_id), "person")

            # --- Scoring Isolation Forest ---
            features = compute_features(track_history[track_id])
            is_anomaly = False
            if features is not None:
                X = np.array([[
                    features["avg_speed"],
                    features["direction_changes_per_sec"],
                    features["stopped_ratio"],
                    features["total_distance"]
                ]])
                score = anomaly_model.decision_function(X)[0]
                is_anomaly = score < 0

            # --- Détection de chute ---
            if is_fallen(bbox):
                if violation_memory[track_id].get("fall") is None:
                    insert_violation(int(track_id), "fall_detected")
                    violation_memory[track_id]["fall"] = now
                    alerts.append((f"⚠ CHUTE ! ID:{track_id}", (0, 0, 255)))

            # --- Détection loitering par comptage de frames ---
            for zone in zones:
                zone_name = zone["name"]
                zone_coords = zone["coords"]
                foot = get_foot_point(bbox)

                if point_in_zone(foot, zone_coords):
                    zone_frame_counter[track_id][zone_name] += 1
                    frames_in_zone = zone_frame_counter[track_id][zone_name]

                    # Déclenche après 30 frames dans la zone
                    if frames_in_zone >= 30:
                        key = f"loitering_{zone_name}"
                        if violation_memory[track_id].get(key) is None:
                            insert_violation(int(track_id), "loitering")
                            violation_memory[track_id][key] = now
                            alerts.append((f"⚠ LOITERING ! ID:{track_id} zone:{zone_name}",
                                          (0, 165, 255)))
                else:
                    # Reset le compteur si la personne quitte la zone
                    zone_frame_counter[track_id][zone_name] = 0

            # --- Dessin bounding box ---
            color = (0, 255, 0)
            if is_anomaly:
                color = (0, 165, 255)
            if is_fallen(bbox):
                color = (0, 0, 255)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, f"ID:{track_id}", (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Ajout des nouvelles alertes à la liste persistante
        now_display = time.time()
        for message, color in alerts:
            persistent_alerts.append((message, color, now_display))

        # Garde seulement les alertes des 3 dernières secondes
        persistent_alerts = [
            (msg, col, t) for msg, col, t in persistent_alerts
            if now_display - t < 3
        ]

        # Affichage des alertes persistantes
        for i, (message, color, _) in enumerate(persistent_alerts):
            draw_alert(frame, message, color, i)

        cv2.imshow("VSI - Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()