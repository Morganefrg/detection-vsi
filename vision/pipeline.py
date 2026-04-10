import cv2
import time
import yaml
import numpy as np
from collections import defaultdict, deque
from ultralytics import YOLO

from vision.utils.capture import get_video_source
from vision.utils.geometry import point_in_zone, get_foot_point, is_fallen
from vision.utils.features import compute_features
from db.repository import insert_tracked_object, insert_violation

# Chargement des zones depuis le fichier YAML
def load_zones(yaml_path: str) -> list:
    """
    Charge les zones de surveillance depuis un fichier YAML.
    """
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return data["zones"]

# Mémoire des violations déjà enregistrées (évite les doublons)
violation_memory = defaultdict(dict)

def run_pipeline(source: str, model_path: str, zones_path: str):
    """
    Lance le pipeline principal de détection et tracking.
    
    source: source vidéo (webcam, fichier, YouTube, RTSP)
    model_path: chemin vers le modèle YOLO
    zones_path: chemin vers le fichier YAML des zones
    """
    # Chargement du modèle YOLO
    model = YOLO(model_path)
    zones = load_zones(zones_path)
    
    # Historique des positions par track_id
    track_history = defaultdict(lambda: deque(maxlen=150))
    
    # Ouverture de la source vidéo
    cap = get_video_source(source)
    if not cap.isOpened():
        print("Erreur : impossible d'ouvrir la source vidéo")
        return

    print("Pipeline démarré. Appuie sur 'q' pour quitter.")

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.03)
            continue

        # Inférence YOLO + ByteTrack
        results = model.track(
            frame,
            persist=True,
            classes=[0],  # classe 0 = personnes
            conf=0.25,
            vid_stride=2
        )

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

            # Mise à jour de l'historique
            track_history[track_id].append((cx, cy, now))

            # Enregistrement dans la base de données
            insert_tracked_object(int(track_id), "person")

            # --- Détection de chute ---
            if is_fallen(bbox):
                if violation_memory[track_id].get("fall") is None:
                    insert_violation(int(track_id), "fall_detected")
                    violation_memory[track_id]["fall"] = now
                    print(f"⚠️ Chute détectée ! track_id={track_id}")

            # --- Détection loitering ---
            for zone in zones:
                zone_coords = zone["coords"]
                foot = get_foot_point(bbox)
                if point_in_zone(foot, zone_coords):
                    if track_id not in violation_memory[track_id]:
                        violation_memory[track_id][f"zone_{zone['name']}"] = now
                    time_in_zone = now - violation_memory[track_id].get(
                        f"zone_{zone['name']}", now
                    )
                    if time_in_zone > 5:  # 5 secondes dans la zone
                        insert_violation(int(track_id), "loitering")
                        violation_memory[track_id][f"zone_{zone['name']}"] = now
                        print(f"⚠️ Loitering détecté ! track_id={track_id}")

            # Dessin de la bounding box
            color = (0, 255, 0)
            if is_fallen(bbox):
                color = (0, 0, 255)  # Rouge si chute
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, f"ID:{track_id}", (int(x1), int(y1)-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imshow("VSI - Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()