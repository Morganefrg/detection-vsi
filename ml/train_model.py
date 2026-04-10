import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

def train_model(csv_path: str, model_output: str):
    """
    Entraîne un modèle Isolation Forest sur les données
    de comportements normaux et le sauvegarde.
    
    csv_path: chemin vers le CSV de données normales
    model_output: chemin où sauvegarder le modèle entraîné
    """
    print(f"Chargement des données depuis {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)} entrées chargées")
    print(f"Features : {list(df.columns)}")

    # Entraînement du modèle
    print("Entraînement du modèle Isolation Forest...")
    model = IsolationForest(
        n_estimators=200,      # 200 arbres
        contamination=0.03,    # 3% de données considérées comme anomalies
        random_state=42        # Pour la reproductibilité
    )
    model.fit(df)

    # Sauvegarde du modèle
    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    joblib.dump(model, model_output)
    print(f"✅ Modèle sauvegardé dans {model_output}")

if __name__ == "__main__":
    train_model(
        csv_path="data/normal_behavior.csv",
        model_output="data/anomaly_model.pkl"
    )