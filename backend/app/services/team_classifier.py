from __future__ import annotations

import logging
import os
from threading import Lock

import cv2
import numpy as np
import torch
import torch.nn.functional as torch_functional
from PIL import Image
from sklearn.cluster import KMeans

from ..schemas import Detection, TeamId


MIN_PLAYERS_FOR_TEAM_SPLIT = 4
MIN_CLUSTER_MARGIN = 0.08
SIGLIP_SOURCE = os.getenv("SIGLIP_SOURCE", "google/siglip-base-patch16-224")

_siglip_lock = Lock()
_siglip_processor = None
_siglip_model = None
_siglip_device: str | None = None
_siglip_status = "lazy"
_siglip_error: str | None = None


def team_classifier_status() -> dict[str, str | None]:
    """Expose whether team grouping uses SigLIP or the color-only fallback."""
    return {"mode": _siglip_status, "error": _siglip_error}


def _load_siglip() -> tuple[object, object, str]:
    global _siglip_processor, _siglip_model, _siglip_device, _siglip_status, _siglip_error
    with _siglip_lock:
        if _siglip_model is not None and _siglip_processor is not None and _siglip_device:
            return _siglip_processor, _siglip_model, _siglip_device
        if _siglip_status == "color_fallback":
            raise RuntimeError(_siglip_error or "SigLIP is unavailable")

        try:
            from transformers import AutoImageProcessor, SiglipVisionModel

            local_files_only = os.getenv("MODEL_OFFLINE") == "1"
            processor = AutoImageProcessor.from_pretrained(
                SIGLIP_SOURCE, local_files_only=local_files_only
            )
            model = SiglipVisionModel.from_pretrained(
                SIGLIP_SOURCE, local_files_only=local_files_only
            )
            # Keep the second vision model off the detector's GPU by default;
            # deployments with spare accelerator memory may override this.
            device = os.getenv("SIGLIP_DEVICE", "cpu")
            model = model.to(device).eval()
            _siglip_processor = processor
            _siglip_model = model
            _siglip_device = device
            _siglip_status = "siglip_ready"
            _siglip_error = None
            return processor, model, device
        except Exception as error:
            _siglip_status = "color_fallback"
            _siglip_error = f"{type(error).__name__}: {error}"
            logging.exception("Could not load SigLIP; using LAB color features only")
            raise


def _siglip_features(shirts: list[np.ndarray]) -> np.ndarray:
    processor, model, device = _load_siglip()
    embeddings: list[np.ndarray] = []
    with _siglip_lock, torch.inference_mode():
        for start in range(0, len(shirts), 8):
            batch = [
                Image.fromarray(cv2.cvtColor(shirt, cv2.COLOR_BGR2RGB))
                for shirt in shirts[start : start + 8]
            ]
            inputs = processor(images=batch, return_tensors="pt").to(device)
            output = model(**inputs).pooler_output
            embeddings.append(torch_functional.normalize(output, dim=-1).cpu().numpy())

    result = np.concatenate(embeddings)
    result -= result.mean(axis=0, keepdims=True)
    result /= np.linalg.norm(result, axis=1, keepdims=True) + 1e-8
    return result


def _shirt_crop(image: np.ndarray, detection: Detection) -> np.ndarray | None:
    box = detection.bbox
    height, width = image.shape[:2]
    x1 = max(0, min(width - 1, int(box.x + box.width * 0.05)))
    x2 = max(x1 + 1, min(width, int(box.x + box.width * 0.95)))
    y1 = max(0, min(height - 1, int(box.y + box.height * 0.12)))
    y2 = max(y1 + 1, min(height, int(box.y + box.height * 0.65)))
    shirt = image[y1:y2, x1:x2]
    return shirt if shirt.size else None


def _jersey_feature(image: np.ndarray, detection: Detection) -> np.ndarray | None:
    """Build the LAB color-histogram feature used by the handoff classifier.

    Detection itself is supplied by the app's existing YOLO detector, so this
    module does not instantiate or load a second copy of best.pt.
    """
    shirt = _shirt_crop(image, detection)
    if shirt is None:
        return None

    lab = cv2.cvtColor(shirt, cv2.COLOR_BGR2LAB)
    histogram = cv2.calcHist(
        [lab], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
    ).ravel()
    histogram = np.sqrt(histogram / (histogram.sum() + 1e-8))
    histogram /= np.linalg.norm(histogram) + 1e-8
    return histogram.astype(np.float64)


def classify_teams(image: np.ndarray, detections: list[Detection]) -> list[Detection]:
    """Group visible players using color histograms and SigLIP embeddings.

    Team A/B are relative groups for this image, not persistent club IDs.
    ``team_confidence`` is a cluster-separation score, not a probability.
    """
    candidate_indices: list[int] = []
    features: list[np.ndarray] = []
    shirts: list[np.ndarray] = []
    for index, detection in enumerate(detections):
        if detection.class_name not in {"player", "goalkeeper"}:
            continue
        feature = _jersey_feature(image, detection)
        if feature is not None:
            candidate_indices.append(index)
            features.append(feature)
            shirt = _shirt_crop(image, detection)
            if shirt is not None:
                shirts.append(shirt)

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

    color_matrix = np.vstack(features)
    try:
        embeddings = _siglip_features(shirts)
        feature_matrix = np.concatenate(
            [np.sqrt(0.65) * color_matrix, np.sqrt(0.35) * embeddings], axis=1
        )
    except Exception:
        # Keep detection and analysis available when the remote or cached
        # SigLIP weights are unavailable; /health reports the fallback mode.
        feature_matrix = color_matrix
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
