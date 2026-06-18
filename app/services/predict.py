# app/services/predict.py
import os
import json
import logging
from typing import Dict, Tuple, Optional

import numpy as np
import tensorflow as tf

# Configure logger for this module
logger = logging.getLogger("predict")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --- CONFIG --- (adjust paths if your project layout differs)
MODEL_WEIGHTS = os.path.join("app", "models", "efficientnet_b1_best.weights.h5")
CLASS_NAMES_FILE = os.path.join("app", "models", "class_names.json")
IMG_SIZE = 224

# Module-level cache
_MODEL: Optional[tf.keras.Model] = None
_CLASS_NAMES: Optional[list] = None


# -------------------------
# Build model architecture
# -------------------------
def _build_model(num_classes: int) -> tf.keras.Model:
    """
    Build the same model architecture used during training.
    """
    base = tf.keras.applications.EfficientNetB1(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3)
    )

    x = tf.keras.layers.GlobalAveragePooling2D()(base.output)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    x = tf.keras.layers.Dense(512, activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs=base.input, outputs=outputs)
    return model


# -------------------------
# Load class names helper
# -------------------------
def _load_class_names(path: str) -> list:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"class names file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Accept either a list or a dict mapping
    if isinstance(data, list):
        class_names = data
    elif isinstance(data, dict):
        # If dict, try to convert to list by index keys or values
        # common cases: {"0": "cat", "1": "dog"} or {"cat": 0, ...}
        # Prefer {index: name}
        try:
            # keys that look like ints
            items = sorted(
                ((int(k), v) for k, v in data.items() if str(k).isdigit()),
                key=lambda kv: kv[0]
            )
            if items:
                class_names = [v for _, v in items]
            else:
                # fallback to values list
                class_names = list(data.values())
        except Exception:
            class_names = list(data.values())
    else:
        raise TypeError("Unsupported class_names.json format; expected list or dict")

    if not class_names:
        raise ValueError("Loaded class names are empty")

    return class_names


# -------------------------
# Initialize / lazy load
# -------------------------
def _init_model_and_classes():
    global _MODEL, _CLASS_NAMES

    if _MODEL is not None and _CLASS_NAMES is not None:
        return _MODEL, _CLASS_NAMES

    # Load class names first (number of classes required to build model)
    try:
        class_names = _load_class_names(CLASS_NAMES_FILE)
        logger.info("✅ Loaded class names (%d classes).", len(class_names))
    except Exception as e:
        logger.error("❌ Failed to load class names: %s", e)
        raise

    # Build model architecture and load weights
    try:
        model = _build_model(len(class_names))
    except Exception as e:
        logger.error("❌ Failed to build model architecture: %s", e)
        raise

    if not os.path.isfile(MODEL_WEIGHTS):
        logger.error("❌ Model weights file not found: %s", MODEL_WEIGHTS)
        raise FileNotFoundError(MODEL_WEIGHTS)

    try:
        # load weights (expects weights saved with model.save_weights(path))
        model.load_weights(MODEL_WEIGHTS)
    except Exception as e:
        logger.error("❌ Failed to load model weights: %s", e)
        raise

    # warm up (optional, small predict to build graph / avoid first-call latency)
    try:
        dummy = np.zeros((1, IMG_SIZE, IMG_SIZE, 3), dtype=np.float32)
        # use preprocess_input to match training preprocessing
        dummy = tf.keras.applications.efficientnet.preprocess_input(dummy)
        _ = model.predict(dummy, verbose=0)
    except Exception:
        # Not fatal; continue
        pass

    _MODEL = model
    _CLASS_NAMES = class_names
    logger.info("✅ Model and weights loaded successfully.")

    return _MODEL, _CLASS_NAMES


# -------------------------
# Prediction helper
# -------------------------
def predict_image(image_path: str) -> Dict[str, object]:
    """
    Predict a single image file.
    Returns: { "condition": <class_name>, "confidence": <float_percent> }
    Throws exception on error.
    """
    model, class_names = _init_model_and_classes()

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Load & preprocess image
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=(IMG_SIZE, IMG_SIZE))
    arr = tf.keras.preprocessing.image.img_to_array(img)
    arr = np.expand_dims(arr, axis=0)

    # Use EfficientNet preprocess_input (scales to model expectation)
    arr = tf.keras.applications.efficientnet.preprocess_input(arr)

    # Predict probabilities
    preds = model.predict(arr, verbose=0)
    if preds is None or preds.shape[-1] != len(class_names):
        # Defensive: if shapes mismatch
        raise RuntimeError("Model prediction shape mismatch or empty prediction.")

    preds = preds[0]  # probability vector
    top_idx = int(np.argmax(preds))
    top_prob = float(preds[top_idx])

    # safety clamp and convert to percent
    confidence_pct = round(max(0.0, min(1.0, top_prob)) * 100.0, 2)

    return {
        "condition": class_names[top_idx],
        "confidence": confidence_pct
    }


# -------------------------
# Router-friendly wrapper
# -------------------------
def predict_condition(image_path: str) -> Tuple[Optional[str], Optional[float], Optional[str]]:
    """
    This returns a simple tuple for compatibility with existing code:
      (condition_name | None, confidence_percent | None, error_message | None)

    If success: (condition, confidence, None)
    If failure: (None, None, "error message")
    """
    try:
        result = predict_image(image_path)
        return result["condition"], result["confidence"], None
    except Exception as e:
        logger.exception("Prediction failed:")
        return None, None, str(e)


# -------------------------
# CLI / local test
# -------------------------
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--img", required=False, default="test.jpg", help="Image file to predict")
    args = p.parse_args()

    try:
        cond, conf, err = predict_condition(args.img)
        if err:
            print("ERROR:", err)
        else:
            print("Prediction:", cond, f"{conf}%")
    except Exception as e:
        print("Fatal:", e)
