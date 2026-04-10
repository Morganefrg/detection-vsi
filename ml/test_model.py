import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import joblib
import numpy as np

def test_model(csv_path: str, model_path: str):
    """
    Teste le modèle Isolation Forest sur les données collectées
    et affiche les statistiques de détection.
    """
    print("Chargement des données...")
    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)} entrées chargées")

    print("Chargement du modèle...")
    model = joblib.load(model_path)

    print("Scoring en cours...")
    scores = model.decision_function(df)
    predictions = model.predict(df)

    # -1 = anomalie, 1 = normal
    nb_anomalies = (predictions == -1).sum()
    nb_normaux = (predictions == 1).sum()
    pct_anomalies = (nb_anomalies / len(df)) * 100

    print(f"\n📊 Résultats :")
    print(f"   Total entrées     : {len(df)}")
    print(f"   Comportements normaux  : {nb_normaux}")
    print(f"   Anomalies détectées    : {nb_anomalies} ({pct_anomalies:.1f}%)")
    print(f"\n   Score min  : {scores.min():.3f}")
    print(f"   Score max  : {scores.max():.3f}")
    print(f"   Score moyen: {scores.mean():.3f}")

    print(f"\n🔍 Exemples d'anomalies détectées :")
    anomalies = df[predictions == -1].head(5)
    print(anomalies.to_string())

if __name__ == "__main__":
    test_model(
        csv_path="data/normal_behavior.csv",
        model_path="data/anomaly_model.pkl"
    )