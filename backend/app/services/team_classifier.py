from __future__ import annotations

import cv2
import numpy as np
from sklearn.cluster import KMeans

from ..schemas import Detection, TeamId


MIN_PLAYERS_FOR_TEAM_SPLIT = 4
MIN_CLUSTER_MARGIN = 0.08


def _jersey_feature(image: np.ndarray, detection: Detection) -> np.ndarray | None:
    """Build the LAB color-histogram feature used by the handoff classifier.

    Detection itself is supplied by the app's existing YOLO detector, so this
    module does not instantiate or load a second copy of best.pt.
    """
    box = detection.bbox
    height, width = image.shape[:2]
    x1 = max(0, min(width - 1, int(box.x + box.width * 0.05)))
    x2 = max(x1 + 1, min(width, int(box.x + box.width * 0.95)))
    y1 = max(0, min(height - 1, int(box.y + box.height * 0.12)))
    y2 = max(y1 + 1, min(height, int(box.y + box.height * 0.65)))
    shirt = image[y1:y2, x1:x2]
    if shirt.size == 0:
        return None

    lab = cv2.cvtColor(shirt, cv2.COLOR_BGR2LAB)
    histogram = cv2.calcHist(
        [lab], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
    ).ravel()
    histogram = np.sqrt(histogram / (histogram.sum() + 1e-8))
    histogram /= np.linalg.norm(histogram) + 1e-8
    return histogram.astype(np.float64)


def classify_teams(image: np.ndarray, detections: list[Detection]) -> list[Detection]:
    """Group visible players by shirt appearance, preserving detector IDs.

    Team A/B are relative groups for this image, not persistent club IDs.
    ``team_confidence`` is a cluster-separation score, not a probability.
    """
    candidate_indices: list[int] = []
    features: list[np.ndarray] = []
    for index, detection in enumerate(detections):
        if detection.class_name not in {"player", "goalkeeper"}:
            continue
        feature = _jersey_feature(image, detection)
        if feature is not None:
            candidate_indices.append(index)
            features.append(feature)

    updated = [
        detection.model_copy(
            update={
                "team_id": None if detection.class_name == "ball" else TeamId.UNASSIGNED,
                "team_confidence": None,
            }
        )
        for detection in detections
    ]

    # With too few samples, two-cluster KMeans can invent a team split.
    if len(features) < MIN_PLAYERS_FOR_TEAM_SPLIT:
        return updated

    feature_matrix = np.vstack(features)
    clusterer = KMeans(n_clusters=2, n_init=20, random_state=42)
    labels = clusterer.fit_predict(feature_matrix)
    distances = clusterer.transform(feature_matrix)

    for feature_index, detection_index in enumerate(candidate_indices):
        ordered = np.sort(distances[feature_index])
        separation = float((ordered[1] - ordered[0]) / (ordered[1] + 1e-8))
        if separation < MIN_CLUSTER_MARGIN:
            continue

        team_id = TeamId.TEAM_A if int(labels[feature_index]) == 0 else TeamId.TEAM_B
        updated[detection_index] = updated[detection_index].model_copy(
            update={
                "team_id": team_id,
                "team_confidence": round(min(1.0, max(0.0, separation)), 3),
            }
        )
    return updated
