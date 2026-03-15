#!/usr/bin/env python3
"""
Alert configuration for Smart Plant Doctor
Defines thresholds and alert settings for sensor data monitoring
"""

# Plant-specific sensor thresholds
PLANT_THRESHOLDS = {
    "Rose": {
        "soil_moisture": {"min": 40, "max": 80, "ideal": 60},
        "temperature": {"min": 15, "max": 25, "ideal": 20},
        "humidity": {"min": 40, "max": 70, "ideal": 55},
        "sunlight": {"min": 6, "max": 8, "ideal": 7}
    },
    "Hibiscus": {
        "soil_moisture": {"min": 50, "max": 85, "ideal": 70},
        "temperature": {"min": 18, "max": 30, "ideal": 24},
        "humidity": {"min": 50, "max": 80, "ideal": 65},
        "sunlight": {"min": 6, "max": 8, "ideal": 7}
    },
    "Aloe Vera": {
        "soil_moisture": {"min": 20, "max": 50, "ideal": 35},
        "temperature": {"min": 15, "max": 30, "ideal": 22},
        "humidity": {"min": 30, "max": 60, "ideal": 45},
        "sunlight": {"min": 4, "max": 6, "ideal": 5}
    },
    "Money Plant": {
        "soil_moisture": {"min": 40, "max": 70, "ideal": 55},
        "temperature": {"min": 15, "max": 25, "ideal": 20},
        "humidity": {"min": 40, "max": 70, "ideal": 55},
        "sunlight": {"min": 2, "max": 4, "ideal": 3}
    },
    "Chrysanthemum": {
        "soil_moisture": {"min": 45, "max": 75, "ideal": 60},
        "temperature": {"min": 10, "max": 20, "ideal": 15},
        "humidity": {"min": 40, "max": 70, "ideal": 55},
        "sunlight": {"min": 6, "max": 8, "ideal": 7}
    },
    "Turmeric": {
        "soil_moisture": {"min": 50, "max": 80, "ideal": 65},
        "temperature": {"min": 20, "max": 35, "ideal": 28},
        "humidity": {"min": 60, "max": 85, "ideal": 75},
        "sunlight": {"min": 4, "max": 6, "ideal": 5}
    }
}

# Alert severity levels
ALERT_LEVELS = {
    "LOW": {
        "color": "#fff3cd",
        "icon": "⚠️",
        "priority": 1
    },
    "MEDIUM": {
        "color": "#f8d7da",
        "icon": "🚨",
        "priority": 2
    },
    "HIGH": {
        "color": "#f5c6cb",
        "icon": "🚨",
        "priority": 3
    },
    "CRITICAL": {
        "color": "#f1b0b7",
        "icon": "🚨",
        "priority": 4
    }
}

# Alert messages templates
ALERT_MESSAGES = {
    "soil_moisture_low": "🌱 {plant_name} needs watering! Soil moisture is {value}% (below {threshold}%)",
    "soil_moisture_high": "💧 {plant_name} is overwatered! Soil moisture is {value}% (above {threshold}%)",
    "temperature_low": "❄️ {plant_name} is too cold! Temperature is {value}°C (below {threshold}°C)",
    "temperature_high": "🔥 {plant_name} is too hot! Temperature is {value}°C (above {threshold}°C)",
    "humidity_low": "🏜️ {plant_name} needs more humidity! Current humidity is {value}% (below {threshold}%)",
    "humidity_high": "💨 {plant_name} has too much humidity! Current humidity is {value}% (above {threshold}%)",
    "sunlight_low": "🌑 {plant_name} needs more sunlight! Current exposure is {value} hours (below {threshold} hours)",
    "sunlight_high": "☀️ {plant_name} is getting too much sun! Current exposure is {value} hours (above {threshold} hours)"
}

# WhatsApp configuration (for future implementation)
WHATSAPP_CONFIG = {
    "enabled": False,  # Set to True when WhatsApp integration is ready
    "api_url": "https://api.whatsapp.com/send",
    "phone_number": "+1234567890"  # Replace with actual phone number
}

# Email configuration (for future implementation)
EMAIL_CONFIG = {
    "enabled": False,  # Set to True when email integration is ready
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "smartplantdoctor@example.com",
    "sender_password": "your_password_here"
}

# Alert settings
ALERT_SETTINGS = {
    "check_interval_minutes": 5,  # How often to check for alerts
    "max_alerts_per_hour": 3,     # Rate limiting
    "alert_cooldown_minutes": 30, # Cooldown between same type alerts
    "enable_sound": True,
    "enable_notifications": True,
    "enable_whatsapp": False,     # Will be enabled when integration is ready
    "enable_email": False         # Will be enabled when integration is ready
}
