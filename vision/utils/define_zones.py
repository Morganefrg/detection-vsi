import cv2
import yaml
import numpy as np

points = []
zones = []
current_zone_name = ""

def click_event(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        print(f"Point ajouté : ({x}, {y})")

def define_zones(video_path: str, output_yaml: str):
    global points, zones, current_zone_name

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Erreur : impossible de lire la vidéo")
        return

    print("\n📋 INSTRUCTIONS :")
    print("- Clique sur l'image pour ajouter des points à la zone")
    print("- Appuie sur 'S' pour sauvegarder la zone courante")
    print("- Appuie sur 'R' pour recommencer la zone courante")
    print("- Appuie sur 'Q' pour terminer et sauvegarder le YAML\n")

    cv2.namedWindow("Définir les zones")
    cv2.setMouseCallback("Définir les zones", click_event)

    while True:
        display = frame.copy()

        # Dessine les zones déjà sauvegardées
        for zone in zones:
            pts = np.array(zone["coords"], dtype=np.int32)
            cv2.polylines(display, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            cx = int(np.mean(pts[:, 0]))
            cy = int(np.mean(pts[:, 1]))
            cv2.putText(display, zone["name"], (cx, cy),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Dessine les points de la zone en cours
        for i, pt in enumerate(points):
            cv2.circle(display, tuple(pt), 5, (0, 0, 255), -1)
            if i > 0:
                cv2.line(display, tuple(points[i-1]), tuple(pt), (0, 0, 255), 2)

        # Ferme le polygone si au moins 3 points
        if len(points) >= 3:
            cv2.line(display, tuple(points[-1]), tuple(points[0]), (0, 0, 255), 1)

        # Instructions sur l'image
        cv2.putText(display, "S=Sauvegarder zone  R=Reset  Q=Terminer",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, f"Points: {len(points)}  Zones: {len(zones)}",
                   (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        cv2.imshow("Définir les zones", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s') and len(points) >= 3:
            current_zone_name = f"zone_{len(zones)+1}"
            zones.append({
                "name": current_zone_name,
                "coords": points.copy()
            })
            print(f"✅ Zone '{current_zone_name}' sauvegardée avec {len(points)} points")
            points = []

        elif key == ord('r'):
            points = []
            print("🔄 Zone réinitialisée")

        elif key == ord('q'):
            break

    cv2.destroyAllWindows()

    if zones:
        with open(output_yaml, "w") as f:
            yaml.dump({"zones": zones}, f, default_flow_style=False)
        print(f"\n✅ {len(zones)} zones sauvegardées dans {output_yaml}")
        for zone in zones:
            print(f"   - {zone['name']} : {len(zone['coords'])} points")
    else:
        print("❌ Aucune zone définie")

if __name__ == "__main__":
    define_zones("data/video_test.mp4", "config/zones.yaml")