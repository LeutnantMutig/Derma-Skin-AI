import tensorflow as tf
from train_b1_best import build_model

IMG_SIZE = 224
NUM_CLASSES = 10
WEIGHTS_PATH = "saved_models/efficientnet_b1_best.weights.h5"

# class names
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


def load_skin_model():
    """Rebuild EfficientNetB1 model and load trained weights."""
    model = build_model(NUM_CLASSES, IMG_SIZE)
    model.load_weights(WEIGHTS_PATH)
    return model, CLASS_NAMES
