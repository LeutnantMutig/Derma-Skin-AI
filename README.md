# 🩺 Derma Skin AI

An AI-powered Skin Disease Classification and Treatment Recommendation System built using **FastAPI, TensorFlow, EfficientNet-B1, Computer Vision, and Deep Learning**.

The system analyzes skin images, predicts the most likely skin disease, stores patient records, and provides treatment recommendations through an interactive web interface.

---

## 🚀 Features

### 🔍 AI-Based Skin Disease Detection

* Upload a skin image
* Automatic disease prediction using Deep Learning
* Confidence score generation
* Fast and accurate inference

### 🏥 Patient Management

* Patient registration
* Patient profile management
* Medical history tracking
* Checkup records management

### 💊 Treatment Recommendation

* Disease-specific treatment suggestions
* Treatment history tracking
* Follow-up recommendations

### 📊 Dashboard & Reports

* Admin Dashboard
* Patient records overview
* Checkup management
* Treatment monitoring

### 🌐 Web Application

* FastAPI backend
* Responsive HTML/CSS frontend
* User authentication system
* Database integration

---

# 🎯 Supported Skin Diseases

The model can classify the following skin diseases:

1. Atopic Dermatitis
2. Basal Cell Carcinoma
3. Benign Keratosis-like Lesions
4. Eczema
5. Fungal Infections
6. Melanocytic Nevi
7. Melanoma
8. Psoriasis & Lichen Planus
9. Seborrheic Keratoses
10. Viral Infections

---

# 🧠 AI Model Details

### Model Architecture

* EfficientNet-B1
* Transfer Learning
* TensorFlow / Keras

### Image Processing

* Image Resizing
* Normalization
* Data Cleaning
* Dataset Splitting

### Input Specifications

| Parameter    | Value           |
| ------------ | --------------- |
| Image Size   | 224 x 224       |
| Channels     | RGB             |
| Framework    | TensorFlow      |
| Architecture | EfficientNet-B1 |

---

# 📂 Dataset Information

### Dataset Overview

* Total Images: 8400+
* Classes: 10
* Medical Dermatology Images
* Balanced Multi-Class Classification Dataset

### Dataset Pipeline

Raw Dataset
↓
Data Cleaning
↓
Image Resizing
↓
Train / Validation / Test Split
↓
Model Training
↓
Evaluation
↓
Deployment

---

# 🏗️ Project Structure

```text
DERMA-SKIN-AI/
│
├── app/
│   ├── models/
│   │   ├── class_names.json
│   │   ├── efficientnet_b1_best.weights.h5
│   │   └── skin_model_arch.json
│   │
│   ├── routers/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── checkups.py
│   │   ├── pages.py
│   │   ├── patients.py
│   │   ├── treatment_dashboard.py
│   │   └── treatments.py
│   │
│   ├── services/
│   │   └── predict.py
│   │
│   ├── static/
│   ├── templates/
│   │
│   ├── database.py
│   ├── db_models.py
│   ├── evaluate.py
│   ├── export_architecture.py
│   ├── export_full_model.py
│   ├── main.py
│   ├── model_loader.py
│   ├── train_b1_best.py
│   └── __init__.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 🛠️ Technology Stack

### Backend

* FastAPI
* Python

### Machine Learning

* TensorFlow
* Keras
* EfficientNet-B1

### Computer Vision

* OpenCV
* NumPy

### Database

* SQLite

### Frontend

* HTML5
* CSS3
* Jinja2 Templates

### Development Tools

* VS Code
* Git
* GitHub

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/LeutnantMutig/Derma-Skin-AI.git
cd Derma-Skin-AI
```

## Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Application

Start FastAPI Server

```bash
uvicorn app.main:app --reload
```

Open Browser:

```text
http://127.0.0.1:8000
```

---

# 📈 Model Performance

### Architecture

* EfficientNet-B1

### Classification Type

* Multi-Class Classification

### Classes

* 10 Skin Disease Categories

### Validation Accuracy

* 70%+

### Framework

* TensorFlow / Keras

---

# 📸 Application Screenshots

## Home Page

```text
screenshots\Home.png"
```

## Prediction Page

```text
screenshots\Prediction.png"
```

## Result Page

```text
screenshots\Result.png"
```

## Dashboard

```text
screenshots\Dashboard.png"
```

## Admin Page 

```
screenshots\Admin.png"
```

## Patient Registration

```
screenshots\Patient Registration.png"
```

---

# 🔒 Disclaimer

This project is intended for educational, research, and demonstration purposes only.

It is not a replacement for professional medical diagnosis, treatment, or healthcare advice.

Always consult a qualified medical professional for clinical decisions.

---

# 🌟 Future Improvements

* Increase model accuracy beyond 90%
* Mobile application integration
* Cloud deployment
* Multi-language support
* Explainable AI (XAI)
* Advanced medical report generation
* Real-time image analysis

---

# 👨‍💻 Author

### Chirag Pawar

B.Tech Computer Science Engineering (AI & ML)

Skills:

* Artificial Intelligence
* Machine Learning
* Deep Learning
* Computer Vision
* Python Development
* FastAPI
* TensorFlow

GitHub:
https://github.com[/LeutnantMutig](https://github.com/LeutnantMutig)

LinkedIn:
[www.linkedin.com/in/chiragpawar01](http://www.linkedin.com/in/chiragpawar01)

---

# ⭐ Support

If you found this project useful, consider giving it a star on GitHub.

⭐ Star the repository
🍴 Fork the project
📢 Share with others
