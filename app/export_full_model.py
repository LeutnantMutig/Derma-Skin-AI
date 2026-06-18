import tensorflow as tf
from train_b1_best import build_model
import json

IMG_SIZE = 224
NUM_CLASSES = 10

# where your weights are saved
WEIGHTS_PATH = "saved_models/efficientnet_b1_best.weights.h5"

# where full model should be saved
FULL_MODEL_PATH = "app/models/skin_model.keras"
CLASS_NAMES_PATH = "app/models/class_names.json"

# your class names
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

print("🔨 Building model...")
model = build_model(NUM_CLASSES, IMG_SIZE)

print("🔄 Loading trained weights...")
model.load_weights(WEIGHTS_PATH)

print("💾 Saving full Keras model...")
model.save(FULL_MODEL_PATH)

print("💬 Saving class names...")
with open(CLASS_NAMES_PATH, "w") as f:
    json.dump(CLASS_NAMES, f)

print("🎉 DONE! Full model exported:")
print("➡", FULL_MODEL_PATH)
