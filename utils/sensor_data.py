"""
Sensor data utilities for Smart Plant Doctor
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

def generate_mock_sensor_data(plant_type: str = "Money Plant") -> Dict:
    """
    Generate mock sensor data for demonstration
    
    Args:
        plant_type: Type of plant for realistic data generation
        
    Returns:
        Dictionary containing sensor readings
    """
    now = datetime.now()
    
    # Base values with some randomness
    base_temp = random.uniform(20, 28)
    base_humidity = random.uniform(45, 75)
    base_light = random.uniform(300, 800)
    base_moisture = random.uniform(35, 65)
    base_ph = random.uniform(6.2, 7.2)
    base_nutrients = random.uniform(65, 85)
    
    data = {
        'timestamp': now,
        'temperature': round(base_temp, 1),
        'humidity': round(base_humidity, 1),
        'light': round(base_light, 0),
        'soil_moisture': round(base_moisture, 1),
        'ph': round(base_ph, 1),
        'nutrients': round(base_nutrients, 1),
        'plant_type': plant_type
    }
    
    return data

def generate_sensor_history(hours: int = 24, plant_type: str = "Money Plant") -> pd.DataFrame:
    """
    Generate historical sensor data
    
    Args:
        hours: Number of hours of historical data
        plant_type: Type of plant
        
    Returns:
        DataFrame with historical sensor data
    """
    data_points = []
    base_time = datetime.now() - timedelta(hours=hours)
    
    for i in range(hours):
        # Generate data with some time-based patterns
        time_offset = timedelta(hours=i)
        current_time = base_time + time_offset
        
        # Simulate day/night cycle for light
        hour_of_day = current_time.hour
        if 6 <= hour_of_day <= 18:  # Daytime
            light_factor = 1.0
            temp_factor = 1.0
        else:  # Nighttime
            light_factor = 0.1
            temp_factor = 0.8
        
        # Generate data with patterns
        data = generate_mock_sensor_data(plant_type)
        data['timestamp'] = current_time
        data['light'] = round(data['light'] * light_factor, 0)
        data['temperature'] = round(data['temperature'] * temp_factor, 1)
        
        data_points.append(data)
    
    return pd.DataFrame(data_points)

def get_plant_health_score(sensor_data: Dict) -> int:
    """
    Calculate plant health score based on sensor data
    
    Args:
        sensor_data: Current sensor readings
        
    Returns:
        Health score (0-100)
    """
    score = 100
    
    # Temperature scoring (20-25°C ideal)
    temp = sensor_data.get('temperature', 22)
    if temp < 15 or temp > 30:
        score -= 30
    elif temp < 18 or temp > 28:
        score -= 15
    elif temp < 20 or temp > 25:
        score -= 5
    
    # Humidity scoring (40-70% ideal)
    humidity = sensor_data.get('humidity', 55)
    if humidity < 30 or humidity > 80:
        score -= 25
    elif humidity < 40 or humidity > 70:
        score -= 10
    
    # Light scoring (300-800 lux ideal)
    light = sensor_data.get('light', 500)
    if light < 200 or light > 1000:
        score -= 20
    elif light < 300 or light > 800:
        score -= 10
    
    # Soil moisture scoring (30-60% ideal)
    moisture = sensor_data.get('soil_moisture', 45)
    if moisture < 20 or moisture > 80:
        score -= 25
    elif moisture < 30 or moisture > 60:
        score -= 10
    
    # pH scoring (6.0-7.0 ideal)
    ph = sensor_data.get('ph', 6.5)
    if ph < 5.5 or ph > 8.0:
        score -= 20
    elif ph < 6.0 or ph > 7.0:
        score -= 10
    
    return max(0, min(100, score))

def get_plant_recommendations(sensor_data: Dict) -> List[str]:
    """
    Get plant care recommendations based on sensor data
    
    Args:
        sensor_data: Current sensor readings
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    temp = sensor_data.get('temperature', 22)
    humidity = sensor_data.get('humidity', 55)
    light = sensor_data.get('light', 500)
    moisture = sensor_data.get('soil_moisture', 45)
    ph = sensor_data.get('ph', 6.5)
    
    # Temperature recommendations
    if temp < 18:
        recommendations.append("🌡️ Move plant to a warmer location")
    elif temp > 28:
        recommendations.append("🌡️ Provide shade or move to cooler area")
    
    # Humidity recommendations
    if humidity < 40:
        recommendations.append("💨 Increase humidity with misting or humidifier")
    elif humidity > 80:
        recommendations.append("💨 Improve air circulation to reduce humidity")
    
    # Light recommendations
    if light < 300:
        recommendations.append("🌞 Move plant to a brighter location")
    elif light > 1000:
        recommendations.append("🌞 Provide some shade to protect from intense light")
    
    # Moisture recommendations
    if moisture < 30:
        recommendations.append("💧 Water your plant - soil is dry")
    elif moisture > 70:
        recommendations.append("💧 Reduce watering frequency - soil is too wet")
    
    # pH recommendations
    if ph < 6.0:
        recommendations.append("🧪 Add lime to increase soil pH")
    elif ph > 7.5:
        recommendations.append("🧪 Add sulfur to decrease soil pH")
    
    # General recommendations if all conditions are good
    if not recommendations:
        recommendations.append("✅ All conditions are optimal - keep up the good work!")
    
    return recommendations

def save_sensor_data(data: Dict, filename: str = "sensor_data.json"):
    """
    Save sensor data to file
    
    Args:
        data: Sensor data dictionary
        filename: Output filename
    """
    filepath = os.path.join("data", filename)
    os.makedirs("data", exist_ok=True)
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

def load_sensor_data(filename: str = "sensor_data.json") -> Optional[Dict]:
    """
    Load sensor data from file
    
    Args:
        filename: Input filename
        
    Returns:
        Sensor data dictionary or None if file doesn't exist
    """
    filepath = os.path.join("data", filename)
    
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return None
