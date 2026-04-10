import cv2
import yt_dlp

def get_video_source(source: str):
    """
    Ouvre une source vidéo — fichier local, webcam, RTSP ou YouTube.
    Retourne un objet VideoCapture OpenCV.
    
    source: 
        - "0" pour la webcam
        - un chemin vers un fichier .mp4
        - une URL YouTube
        - une URL RTSP
    """
    # Webcam
    if source == "0":
        cap = cv2.VideoCapture(0)
        print("Source : webcam")
        return cap

    # YouTube
    if "youtube.com" in source or "youtu.be" in source:
        print("Source : YouTube, récupération de l'URL...")
        ydl_opts = {"quiet": True, "format": "best[ext=mp4]"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source, download=False)
            url = info["url"]
        cap = cv2.VideoCapture(url)
        print("Source : YouTube OK")
        return cap

    # Fichier local ou RTSP
    cap = cv2.VideoCapture(source)
    print(f"Source : {source}")
    return cap