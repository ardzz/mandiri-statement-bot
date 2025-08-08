import os
from typing import List, Tuple

import numpy as np
from joblib import dump, load
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """Simple wrapper around IsolationForest for spending anomaly detection."""

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.model: IsolationForest | None = None
        if os.path.exists(self.model_path):
            try:
                self.model = load(self.model_path)
            except Exception:
                self.model = None

    @property
    def is_trained(self) -> bool:
        return self.model is not None

    def train(self, amounts: List[float]) -> None:
        """Train model on list of spending amounts and persist to disk."""
        if not amounts:
            raise ValueError("No data provided for training")

        X = np.array(amounts).reshape(-1, 1)
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.model.fit(X)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        dump(self.model, self.model_path)

    def predict(self, amounts: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        """Run inference on amounts. Returns predictions and anomaly scores."""
        if not self.model:
            raise ValueError("Model not trained")

        X = np.array(amounts).reshape(-1, 1)
        preds = self.model.predict(X)
        scores = self.model.decision_function(X)
        return preds, scores
