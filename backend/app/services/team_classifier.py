from __future__ import annotations

import cv2
import numpy as np
from sklearn.cluster import KMeans

from ..schemas import Detection, TeamId


def _jersey_feature(image: np.ndarray, detection: Detection) -> np.ndarray | None:
    box = detection.bbox
    height, width = image.shape[:2]
    x1 = max(0, min(width - 1, int(box.x + box.width * 0.2)))
    x2 = max(x1 + 1, min(width, int(box.x + box.width * 0.8)))
    y1 = max(0, min(height - 1, int(box.y + box.height * 0.12)))
    y2 = max(y1 + 1, min(height, int(box.y + box.height * 0.55)))
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape(-1, 3)
    non_grass = pixels[
        ~(
            (pixels[:, 0] >= 28)
            & (pixels[:, 0] <= 95)
            & (pixels[:, 1] >= 35)
        )
    ]
    useful = non_grass[non_grass[:, 2] >= 35]
    if len(useful) < 12:
        return None

    hue_hist, _ = np.histogram(useful[:, 0], bins=12, range=(0, 180), density=True)
    sat_mean = useful[:, 1].mean() / 255.0
    val_mean = useful[:, 2].mean() / 255.0
    return np.concatenate([hue_hist, [sat_mean, val_mean]]).astype(np.float64)


def classify_teams(image: np.ndarray, detections: list[Detection]) -> list[Detection]:
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
    if len(features) < 2:
        return updated

    feature_matrix = np.vstack(features)
    model = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = model.fit_predict(feature_matrix)
    center_order = np.argsort(model.cluster_centers_[:, :12].argmax(axis=1))
    label_to_team = {
        int(center_order[0]): TeamId.TEAM_A,
        int(center_order[1]): TeamId.TEAM_B,
    }
    distances = model.transform(feature_matrix)

    for feature_index, detection_index in enumerate(candidate_indices):
        assigned_label = int(labels[feature_index])
        sorted_distances = np.sort(distances[feature_index])
        confidence = 1.0
        if len(sorted_distances) > 1 and sorted_distances[1] > 0:
            confidence = max(0.0, min(1.0, 1 - sorted_distances[0] / sorted_distances[1]))
        updated[detection_index] = updated[detection_index].model_copy(
            update={
                "team_id": label_to_team[assigned_label],
                "team_confidence": round(float(confidence), 3),
            }
        )
    return updated

