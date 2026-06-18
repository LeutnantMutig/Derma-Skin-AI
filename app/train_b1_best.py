import os
import argparse
import tensorflow as tf
from tensorflow.keras.preprocessing import image_dataset_from_directory
from tensorflow.keras.applications import EfficientNetB1
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# ------------------------------------------------
# GPU MEMORY GROWTH
# ------------------------------------------------
gpus = tf.config.list_physical_devices("GPU")
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print("✅ Enabled GPU memory growth")
else:
    print("⚠ No GPU found — using CPU")


# ------------------------------------------------
# MODEL BUILDER
# ------------------------------------------------
def build_model(num_classes, img_size):
    base = EfficientNetB1(
        include_top=False,
        weights="imagenet",
        input_shape=(img_size, img_size, 3)
    )

    base.trainable = False  # Stage 1 frozen

    x = GlobalAveragePooling2D()(base.output)
    x = BatchNormalization()(x)
    x = Dropout(0.4)(x)
    x = Dense(512, activation="relu")(x)
    x = BatchNormalization()(x)
    x = Dropout(0.3)(x)

    outputs = Dense(num_classes, activation="softmax")(x)
    return Model(inputs=base.input, outputs=outputs)


# ------------------------------------------------
# DATA LOADER
# ------------------------------------------------
def load_datasets(data_dir, img_size, batch):
    print("\n🔍 Loading dataset...")

    train_path = os.path.join(data_dir, "train")
    val_path = os.path.join(data_dir, "val")

    train_ds = image_dataset_from_directory(
        train_path,
        label_mode="categorical",
        batch_size=batch,
        image_size=(img_size, img_size),
        shuffle=True
    )

    val_ds = image_dataset_from_directory(
        val_path,
        label_mode="categorical",
        batch_size=batch,
        image_size=(img_size, img_size),
        shuffle=False
    )

    print("✅ Classes found:", train_ds.class_names)

    AUTOTUNE = tf.data.AUTOTUNE
    return train_ds.prefetch(AUTOTUNE), val_ds.prefetch(AUTOTUNE), train_ds.class_names


# ------------------------------------------------
# TRAINING PIPELINE
# ------------------------------------------------
def train(args):

    train_ds, val_ds, class_names = load_datasets(
        args.data_dir, args.img_size, args.batch_size
    )

    num_classes = len(class_names)
    model = build_model(num_classes, args.img_size)

    # ----------------------------
    # STAGE 1 — FROZEN BASE
    # ----------------------------
    print("\n🔵 Stage 1: Training top layers (base frozen)\n")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    early_stop = EarlyStopping(
        monitor="val_accuracy",
        patience=10,
        restore_best_weights=True
    )

    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.4,
        patience=4,
        min_lr=1e-6,
        verbose=1
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )

    # ----------------------------
    # SAVE WEIGHTS (NO JSON BUG)
    # ----------------------------
    print("\n💾 Saving stage-1 model weights...")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    model.save_weights(args.output)
    print("✅ Saved weights:", args.output)

    # ----------------------------
    # STAGE 2 — FINE TUNING
    # ----------------------------
    print("\n🟣 Stage 2: Fine-tuning entire model\n")

    for layer in model.layers:
        layer.trainable = True

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.fine_tune_epochs,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )

    print("\n💾 Saving final fine-tuned weights...")
    model.save_weights(args.output)
    print("🎉 Training complete! Final weights saved:", args.output)


# ------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--img-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--fine-tune-epochs", type=int, default=40)
    parser.add_argument("--output", type=str, default="saved_models/efficientnet_b1_best.weights.h5")

    args = parser.parse_args()
    train(args)
