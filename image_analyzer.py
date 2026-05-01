"""
Image Analyzer Module
Provides preprocessing, enhancement, OCR, and simple coin/inscription helpers
for archaeological artifact images.

This module avoids destructive edits by returning enhanced copies.
"""

from typing import Dict, List, Tuple, Optional
import io

import numpy as np
from PIL import Image

# Optional heavy deps are imported lazily to keep startup fast
import cv2


SCRIPT_PROFILES: Dict[str, Dict[str, object]] = {
    "auto": {
        "label": "Auto / mixed",
        "languages": ["en"],
        "notes": "Best-effort OCR with generic Latin support and manual review cues.",
    },
    "latin": {
        "label": "Latin / Roman legends",
        "languages": ["en"],
        "notes": "Optimized for Romanized legends and worn coin inscriptions.",
    },
    "greek": {
        "label": "Greek",
        "languages": ["el", "en"],
        "notes": "Uses modern Greek OCR where available; ancient forms still need manual review.",
    },
    "devanagari": {
        "label": "Devanagari variants",
        "languages": ["hi", "en"],
        "notes": "Uses Hindi OCR as a best-effort proxy for Devanagari-derived scripts.",
    },
    "brahmi": {
        "label": "Brahmi / early scripts",
        "languages": ["en"],
        "notes": "No bundled specialist model; use enhancement plus hotspot review and manual correction.",
    },
    "kharoshthi": {
        "label": "Kharoshthi",
        "languages": ["en"],
        "notes": "No bundled specialist model; use enhancement plus hotspot review and manual correction.",
    },
}


def get_script_profiles() -> Dict[str, Dict[str, object]]:
    """Expose script profiles to the UI without importing app modules."""
    return SCRIPT_PROFILES


def pil_to_cv(image: Image.Image) -> np.ndarray:
    """Convert PIL image to OpenCV BGR array."""
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    arr = np.array(image)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def cv_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR/GRAY array to PIL."""
    if len(arr.shape) == 2:
        return Image.fromarray(arr)
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def preprocess(image: Image.Image) -> Dict[str, Image.Image]:
    """Basic preprocessing: denoise, contrast, shadow reduction, normalization.

    Returns a dict of intermediate results for inspection.
    """
    cv = pil_to_cv(image)

    # Denoise (fast non-local means)
    denoised = cv2.fastNlMeansDenoisingColored(cv, None, h=6, hColor=6, templateWindowSize=7, searchWindowSize=21)

    # Shadow reduction via morphological opening on value channel
    hsv = cv2.cvtColor(denoised, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    background = cv2.morphologyEx(v, cv2.MORPH_OPEN, kernel)
    v2 = cv2.subtract(v, background)
    hsv[:, :, 2] = cv2.normalize(v2, None, 0, 255, cv2.NORM_MINMAX)
    shadow_reduced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Gray-world color normalization
    avg_b, avg_g, avg_r = np.mean(shadow_reduced.reshape(-1, 3), axis=0)
    k = (avg_r + avg_g + avg_b) / 3.0
    gain_b = k / (avg_b + 1e-6)
    gain_g = k / (avg_g + 1e-6)
    gain_r = k / (avg_r + 1e-6)
    norm = shadow_reduced.copy().astype(np.float32)
    norm[:, :, 0] *= gain_b
    norm[:, :, 1] *= gain_g
    norm[:, :, 2] *= gain_r
    norm = np.clip(norm, 0, 255).astype(np.uint8)

    return {
        "denoised": cv_to_pil(denoised),
        "shadow_reduced": cv_to_pil(shadow_reduced),
        "normalized": cv_to_pil(norm),
    }


def enhance_clahe(image: Image.Image) -> Image.Image:
    """Contrast Limited Adaptive Histogram Equalization on L channel."""
    cv = pil_to_cv(image)
    lab = cv2.cvtColor(cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    out = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    return cv_to_pil(out)


def enhance_retinex(image: Image.Image, scales: Tuple[int, int, int] = (15, 80, 250)) -> Image.Image:
    """Multi-Scale Retinex for illumination correction."""
    cv = pil_to_cv(image)
    cv_float = cv.astype(np.float32) + 1.0
    result = np.zeros_like(cv_float)
    for scale in scales:
        blur = cv2.GaussianBlur(cv_float, (0, 0), sigmaX=scale, sigmaY=scale)
        result += np.log(cv_float) - np.log(blur)
    result /= float(len(scales))
    # Color restoration
    intensity = cv2.cvtColor(cv.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) + 1.0
    crom = 125 * (np.log(125 * cv_float) - np.log(intensity[:, :, None]))
    result = result * crom
    # Normalize to 0-255
    for c in range(3):
        chan = result[:, :, c]
        chan = (chan - np.min(chan)) / (np.max(chan) - np.min(chan) + 1e-6)
        result[:, :, c] = chan * 255.0
    result = np.clip(result, 0, 255).astype(np.uint8)
    return cv_to_pil(result)


def enhance_sharpen(image: Image.Image) -> Image.Image:
    """Simple unsharp masking to highlight edges and inscriptions."""
    cv = pil_to_cv(image)
    blur = cv2.GaussianBlur(cv, (0, 0), sigmaX=1.5, sigmaY=1.5)
    sharp = cv2.addWeighted(cv, 1.6, blur, -0.6, 0)
    return cv_to_pil(sharp)


def hough_coin_detection(image: Image.Image) -> Dict:
    """Detect circular coin-like shapes using Hough transform."""
    cv = pil_to_cv(image)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    rows = gray.shape[0]
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=rows / 8,
        param1=80, param2=30, minRadius=int(rows * 0.1), maxRadius=int(rows * 0.9)
    )
    coins: List[Tuple[int, int, int]] = []
    if circles is not None:
        coins = [(int(x), int(y), int(r)) for x, y, r in np.round(circles[0, :]).astype("int")]
    return {"circles": coins}


def _candidate_readings(text: str, script_profile: str) -> List[str]:
    """Generate top candidate readings for damaged or noisy OCR output."""
    base = (text or "").strip()
    if not base:
        return ["Unreadable segment", "Damaged inscription", "Manual review needed"]

    normalized = "".join(ch for ch in base.upper() if ch.isalnum() or ch in {"-", "/", " "}).strip()
    substitutions = normalized.replace("0", "O").replace("1", "I").replace("5", "S")
    profile_hint = f"{normalized} ({script_profile})" if script_profile not in {"auto", "latin"} else normalized

    ordered = []
    for candidate in [base, normalized or base, substitutions or normalized, profile_hint]:
        if candidate and candidate not in ordered:
            ordered.append(candidate)
    return ordered[:3]


def run_ocr(image: Image.Image, script_profile: str = "auto", languages: Optional[List[str]] = None) -> Dict[str, object]:
    """Run OCR if available and return regions, backend, and review hints."""
    profile = SCRIPT_PROFILES.get(script_profile, SCRIPT_PROFILES["auto"])
    langs = languages or list(profile.get("languages", ["en"]))
    try:
        import easyocr  # type: ignore
        reader = easyocr.Reader(langs, gpu=False)
        arr = np.array(image.convert("RGB"))
        results = reader.readtext(arr)
        regions = []
        for index, (bbox, text, conf) in enumerate(results, start=1):
            # bbox: 4 points, convert to rectangle
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            x_min, x_max = int(min(xs)), int(max(xs))
            y_min, y_max = int(min(ys)), int(max(ys))
            regions.append({
                "hotspot_id": index,
                "box": [x_min, y_min, x_max, y_max],
                "text": text,
                "confidence": float(conf),
                "top_candidates": _candidate_readings(text, script_profile),
            })
        return {
            "regions": regions,
            "backend": "easyocr",
            "script_profile": script_profile,
            "notes": str(profile.get("notes", "")),
        }
    except Exception:
        # Fallback: simple edge-based pseudo boxes (no text)
        cv = pil_to_cv(image)
        gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 120)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        for index, cnt in enumerate(contours[:25], start=1):  # limit
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 300:  # skip tiny
                regions.append(
                    {
                        "hotspot_id": index,
                        "box": [x, y, x + w, y + h],
                        "text": "",
                        "confidence": 0.0,
                        "top_candidates": _candidate_readings("", script_profile),
                    }
                )
        return {
            "regions": regions,
            "backend": "contour-fallback",
            "script_profile": script_profile,
            "notes": "OCR package unavailable or unsupported for this script; showing candidate hotspots for manual reading.",
        }


def draw_boxes(image: Image.Image, boxes: List[Dict]) -> Image.Image:
    """Overlay bounding boxes and indices on image."""
    cv = pil_to_cv(image)
    for i, b in enumerate(boxes):
        x1, y1, x2, y2 = b["box"]
        cv2.rectangle(cv, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{i+1}"
        cv2.putText(cv, label, (x1, max(y1-5, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    return cv_to_pil(cv)


def crop_box(image: Image.Image, box: List[int]) -> Image.Image:
    """Return a zoomed crop for a selected bounding box."""
    x1, y1, x2, y2 = box
    return image.crop((x1, y1, x2, y2))


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def analyze(image: Image.Image, script_profile: str = "auto") -> Dict:
    """High-level analysis pipeline. Returns dict of outputs.
    - preprocessing variants
    - enhancements: CLAHE, Retinex, Sharpen
    - coin circle detection
    - OCR boxes
    """
    pre = preprocess(image)
    clahe = enhance_clahe(pre.get("normalized", image))
    retinex = enhance_retinex(pre.get("normalized", image))
    sharp = enhance_sharpen(pre.get("normalized", image))

    ocr_payload = run_ocr(retinex, script_profile=script_profile)  # OCR on retinex variant typically performs better
    boxed = draw_boxes(retinex, ocr_payload["regions"])

    coin = hough_coin_detection(image)

    return {
        "preprocessed": pre,
        "enhancements": {
            "clahe": clahe,
            "retinex": retinex,
            "sharpen": sharp,
        },
        "ocr": ocr_payload,
        "boxed": boxed,
        "coin": coin,
    }
