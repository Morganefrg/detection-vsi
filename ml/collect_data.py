import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import time
import csv
from collections import defaultdict, deque
from ultralytics import YOLO

from vision.utils.features import compute_features

def collect_normal_data(source: str, output_csv: str, model_path: str = "yolo11n.pt"):
    """
    Fait tourner le pipeline sur une vidéo et enregistre
    les features comportementales dans un fichier CSV.
    Ce CSV servira à entraîner l'Isolation Forest.
    """
    model = YOLO(model_path)
    track_history = defaultdict(lambda: deque(maxlen=150))

    # Crée le dossier data si nécessaire
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("Erreur : impossible d'ouvrir la source vidéo")
        return

    print(f"Collecte des données depuis : {source}")
    print("Appuie sur 'q' pour arrêter...")

    rows = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            frame,
            persist=True,
            classes=[0],
            conf=0.25,
            vid_stride=4,
            imgsz=320
        )

        if results[0].boxes.id is None:
            continue

        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)

        for bbox, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = bbox
            cx = int((x1 + x2) / 2)
            cy = int(y2)
            now = time.time()

            track_history[track_id].append((cx, cy, now))

            # Calcule les features si assez d'historique
            features = compute_features(track_history[track_id])
            if features is not None:
                rows.append([
                    features["avg_speed"],
                    features["direction_changes_per_sec"],
                    features["stopped_ratio"],
                    features["total_distance"]
                ])

        cv2.imshow("Collecte données", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Sauvegarde dans le CSV
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["avg_speed", "direction_changes_per_sec", "stopped_ratio", "total_distance"])
        writer.writerows(rows)

    print(f"✅ {len(rows)} entrées sauvegardées dans {output_csv}")

if __name__ == "__main__":
    collect_normal_data(
        source="data/video_test.mp4",
        output_csv="data/normal_behavior.csv"
    )