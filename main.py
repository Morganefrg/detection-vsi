import argparse
from vision.pipeline import run_pipeline

def main():
    """
    Point d'entrée principal de l'application VSI.
    """
    parser = argparse.ArgumentParser(description="VSI - Vidéo Surveillance Intelligente")
    
    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Source vidéo : '0' pour webcam, chemin fichier .mp4, ou URL YouTube"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="Chemin vers le modèle YOLO"
    )
    parser.add_argument(
        "--zones",
        type=str,
        default="config/zones.yaml",
        help="Chemin vers le fichier de configuration des zones"
    )

    args = parser.parse_args()

    print(f"Source  : {args.source}")
    print(f"Modèle  : {args.model}")
    print(f"Zones   : {args.zones}")
    print("Démarrage du pipeline...")

    run_pipeline(
        source=args.source,
        model_path=args.model,
        zones_path=args.zones
    )

if __name__ == "__main__":
    main()