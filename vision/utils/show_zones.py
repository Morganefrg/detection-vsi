import cv2
import yaml
import numpy as np

def show_zones(video_path: str, zones_path: str):
    """
    Affiche la première frame de la vidéo avec les zones dessinées dessus.
    Utile pour calibrer les coordonnées des zones.
    """
    # Ouvre la vidéo et récupère la première frame
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Erreur : impossible de lire la vidéo")
        return

    # Affiche les dimensions de la frame
    height, width = frame.shape[:2]
    print(f"Dimensions de la vidéo : {width}x{height} pixels")

    # Charge les zones
    with open(zones_path, "r") as f:
        data = yaml.safe_load(f)

    # Dessine chaque zone sur la frame
    for zone in data["zones"]:
        pts = np.array(zone["coords"], dtype=np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
        # Affiche le nom de la zone
        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        cv2.putText(frame, zone["name"], (cx, cy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Zones de surveillance", frame)
    print("Appuie sur une touche pour fermer...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    show_zones("data/video_test.mp4", "config/zones.yaml")