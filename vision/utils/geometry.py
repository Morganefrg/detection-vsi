import cv2
import numpy as np

def point_in_zone(point: tuple, zone: list) -> bool:
    """
    Vérifie si un point est à l'intérieur d'une zone polygonale.
    
    point: (x, y) — coordonnées du point à tester
    zone: liste de points [(x1,y1), (x2,y2), ...] qui définissent le polygone
    """
    contour = np.array(zone, dtype=np.float32)
    result = cv2.pointPolygonTest(contour, point, False)
    return result >= 0

def get_foot_point(bbox: tuple) -> tuple:
    """
    Retourne le point pied d'une bounding box.
    C'est le point central bas de la bbox — là où la personne touche le sol.
    
    bbox: (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = bbox
    cx = int((x1 + x2) / 2)
    cy = int(y2)
    return (cx, cy)

def is_fallen(bbox: tuple) -> bool:
    """
    Détecte si une personne est tombée en analysant le ratio de sa bounding box.
    Si la largeur est plus grande que la hauteur → la personne est allongée → chute.
    
    bbox: (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    if height == 0:
        return False
    ratio = height / width
    return ratio < 1.0