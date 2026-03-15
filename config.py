"""
Configuration file for Smart Plant Doctor Streamlit App
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
AI_DIR = BASE_DIR / "ai"
MODEL_PATH = AI_DIR / "exports" / "smart_plant_doctor_model.pth"
CLASS_MAPPING_PATH = AI_DIR / "exports" / "class_mapping.json"

# Model configuration
MODEL_CONFIG = {
    "model_path": "ai/exports/smart_plant_doctor_model.pth",
    "device": "auto",  # "auto", "cpu", "cuda"
    "confidence_threshold": 0.35,
    "input_size": 224
}

# Sensor data configuration
SENSOR_CONFIG = {
    "update_interval": 60,  # seconds
    "history_hours": 24,
    "mock_data": True  # Set to False for real sensor data
}

# Plant thresholds for alerts (will be used later)
PLANT_THRESHOLDS = {
    "Money Plant": {
        "temperature": {"min": 18, "max": 25, "ideal": 22},
        "humidity": {"min": 40, "max": 70, "ideal": 55},
        "light": {"min": 200, "max": 800, "ideal": 500},
        "soil_moisture": {"min": 30, "max": 60, "ideal": 45},
        "ph": {"min": 6.0, "max": 7.0, "ideal": 6.5}
    },
    "Rose": {
        "temperature": {"min": 15, "max": 28, "ideal": 22},
        "humidity": {"min": 50, "max": 80, "ideal": 65},
        "light": {"min": 400, "max": 1000, "ideal": 700},
        "soil_moisture": {"min": 40, "max": 70, "ideal": 55},
        "ph": {"min": 6.0, "max": 7.0, "ideal": 6.5}
    },
    "Aloe Vera": {
        "temperature": {"min": 20, "max": 30, "ideal": 25},
        "humidity": {"min": 30, "max": 60, "ideal": 45},
        "light": {"min": 300, "max": 900, "ideal": 600},
        "soil_moisture": {"min": 20, "max": 50, "ideal": 35},
        "ph": {"min": 6.0, "max": 7.5, "ideal": 6.8}
    },
    "Hibiscus": {
        "temperature": {"min": 18, "max": 32, "ideal": 25},
        "humidity": {"min": 40, "max": 70, "ideal": 55},
        "light": {"min": 400, "max": 1000, "ideal": 700},
        "soil_moisture": {"min": 35, "max": 65, "ideal": 50},
        "ph": {"min": 6.0, "max": 7.0, "ideal": 6.5}
    },
    "Chrysanthemum": {
        "temperature": {"min": 15, "max": 25, "ideal": 20},
        "humidity": {"min": 50, "max": 80, "ideal": 65},
        "light": {"min": 300, "max": 800, "ideal": 550},
        "soil_moisture": {"min": 40, "max": 70, "ideal": 55},
        "ph": {"min": 6.0, "max": 7.0, "ideal": 6.5}
    },
    "Turmeric": {
        "temperature": {"min": 20, "max": 30, "ideal": 25},
        "humidity": {"min": 60, "max": 85, "ideal": 72},
        "light": {"min": 300, "max": 700, "ideal": 500},
        "soil_moisture": {"min": 50, "max": 80, "ideal": 65},
        "ph": {"min": 6.0, "max": 7.5, "ideal": 6.8}
    }
}

# UI Configuration
UI_CONFIG = {
    "page_title": "🌱 Smart Plant Doctor",
    "page_icon": "🌱",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "theme": {
        "primary_color": "#2E8B57",
        "background_color": "#FFFFFF",
        "secondary_background_color": "#F0F2F6",
        "text_color": "#262730"
    }
}

# Chart colors
CHART_COLORS = {
    "primary": "#2E8B57",
    "secondary": "#FF6B6B",
    "success": "#4ECDC4",
    "warning": "#FFE66D",
    "danger": "#FF6B6B",
    "info": "#4ECDC4"
}

# Supported file types for image upload
SUPPORTED_IMAGE_TYPES = ['jpg', 'jpeg', 'png']

# Model performance metrics
MODEL_METRICS = {
    "accuracy": 92.37,
    "num_classes": 29,
    "num_plants": 6,
    "input_size": 224,
    "training_images": 45895
}
