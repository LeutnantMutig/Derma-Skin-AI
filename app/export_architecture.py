import tensorflow as tf
import json
from train_b1_best import build_model

IMG_SIZE = 224
NUM_CLASSES = 10

WEIGHTS_PATH = "saved_models/efficientnet_b1_best.weights.h5"
ARCH_PATH = "app/models/skin_model_arch.json"
CLASS_NAMES_PATH = "app/models/class_names.json"

CLASS_NAMES = [
    'Atopic_Dermatitis',
    'Basal_Cell_Carcinoma',
    'Benign_Keratosis_like_Lesions',
    'Eczema',
    'Fungal_Infections',
    'Melanocyti_Nevi',
    'Melanoma',
    'Psoriasis_Lichen_Planus',
    'Seborrheic_Keratoses',
    'Viral_Infections'
]

print("🔨 Building model architecture...")
model = build_model(NUM_CLASSES, IMG_SIZE)

print("🔄 Loading weights...")
model.load_weights(WEIGHTS_PATH)

print("💾 Saving architecture ONLY (no optimizer, no tensors)...")
with open(ARCH_PATH, "w") as f:
    f.write(model.to_json())

print("💬 Saving class names...")
with open(CLASS_NAMES_PATH, "w") as f:
    json.dump(CLASS_NAMES, f)

print("🎉 DONE! Saved:")
print("➡ Architecture:", ARCH_PATH)
print("➡ Weights:", WEIGHTS_PATH)
print("➡ Class names:", CLASS_NAMES_PATH)

