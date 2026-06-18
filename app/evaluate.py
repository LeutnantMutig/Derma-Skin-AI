import numpy as np
import tensorflow as tf
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
import json

model = tf.keras.models.load_model("saved_models/skin_model.keras")

try:
    with open("saved_models/class_names.json") as f:
        class_names = json.load(f)
except Exception:
    class_names = None

# create val dataset 
val_ds = tf.keras.utils.image_dataset_from_directory(
    "dataset/val", image_size=(256,256), batch_size=32, label_mode="int", shuffle=False
)

y_true = []
y_pred = []
for imgs, labels in val_ds:
    preds = model.predict(imgs, verbose=0)
    y_pred.extend(np.argmax(preds, axis=1).tolist())
    y_true.extend(labels.numpy().tolist())

print("Confusion matrix:")
print(confusion_matrix(y_true, y_pred))

print("\nClassification report:")
print(classification_report(y_true, y_pred, target_names=class_names))
