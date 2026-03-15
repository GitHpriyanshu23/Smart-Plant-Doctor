#!/usr/bin/env python3
"""
Smart Plant Doctor - Streamlit Web Application
Combines sensor monitoring and plant disease detection
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import os
import sys
from PIL import Image
import io
import sqlite3
import numpy as np
import math

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_COMPONENT_AVAILABLE = True
except ImportError:
    AUTOREFRESH_COMPONENT_AVAILABLE = False

# Add the project root and ai directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'ai'))

try:
    from inference import SmartPlantDoctor
except ImportError:
    st.error("❌ Could not import SmartPlantDoctor. Make sure inference.py is in the ai/ directory.")
    st.stop()

# Import alert system
try:
    from utils.alert_system import alert_system, Alert
    from alert_config import ALERT_LEVELS, ALERT_SETTINGS

    # WhatsApp is intentionally disabled for now.
    alert_system.disable_whatsapp()

except ImportError as e:
    st.error(f"❌ Could not import alert system: {str(e)}")
    st.error("Make sure alert_system.py is in utils/ directory and alert_config.py is in root directory.")
    st.stop()

# Live sensors DB (populated by ingest.py) - use absolute path anchored to project root
DB_PATH = os.path.join(project_root, "data", "sensors.db")

def _db_exists() -> bool:
    return os.path.exists(DB_PATH)

def get_plants_from_db():
    if not _db_exists():
        return []
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute("SELECT DISTINCT plant FROM readings ORDER BY plant").fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []
    finally:
        con.close()

def get_latest_from_db(plant: str):
    if not _db_exists():
        return None
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(
            "SELECT ts, plant, temperature, humidity, light, soil_moisture, ph FROM readings WHERE plant=? ORDER BY rowid DESC LIMIT 1",
            (plant,),
        )
        row = cur.fetchone()
        if not row:
            return None
        keys = ["ts","plant","temperature","humidity","light","soil_moisture","ph"]
        return dict(zip(keys, row))
    except Exception:
        return None
    finally:
        con.close()

def get_previous_from_db(plant: str):
    if not _db_exists():
        return None
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(
            "SELECT ts, plant, temperature, humidity, light, soil_moisture, ph FROM readings WHERE plant=? ORDER BY rowid DESC LIMIT 1 OFFSET 1",
            (plant,),
        )
        row = cur.fetchone()
        if not row:
            return None
        keys = ["ts", "plant", "temperature", "humidity", "light", "soil_moisture", "ph"]
        return dict(zip(keys, row))
    except Exception:
        return None
    finally:
        con.close()

def _parse_ts_to_datetime(ts_value, fallback_index=0):
    """Convert device timestamp to datetime; fallback to recent synthetic timestamp."""
    try:
        ts_num = float(ts_value)
        # If millis since epoch, scale down to seconds.
        if ts_num > 1e12:
            ts_num = ts_num / 1000.0
        # Epoch sanity check (year 2000+).
        if ts_num > 946684800:
            return datetime.fromtimestamp(ts_num)
    except Exception:
        pass
    return datetime.now() - timedelta(minutes=max(0, fallback_index))

def calculate_health_score(sensor_data: dict) -> int:
    """Estimate health score from current sensor values (0-100)."""
    ranges = {
        'temperature': (18, 28),
        'humidity': (40, 80),
        'light': (200, 1000),
        'soil_moisture': (30, 70),
    }
    penalties = 0.0
    for key, (low, high) in ranges.items():
        value = float(sensor_data.get(key, (low + high) / 2))
        if value < low:
            penalties += min(25.0, ((low - value) / max(1.0, low)) * 25.0)
        elif value > high:
            penalties += min(25.0, ((value - high) / max(1.0, high)) * 25.0)
    return int(max(0, min(100, round(100.0 - penalties))))

def get_soil_condition(moisture_percent: float):
    """Map soil moisture percentage to the same wet/moist/dry states used by firmware."""
    if moisture_percent >= 85:
        return "Wet", "#2E8B57", "🌊"
    if moisture_percent >= 35:
        return "Moist", "#FFC107", "💧"
    return "Dry", "#E53935", "⚠️"

# Page configuration
st.set_page_config(
    page_title="🌱 Smart Plant Doctor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        color: #2c3e50;
        font-weight: 500;
    }
    .treatment-card {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    .health-card {
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        color: #2c3e50;
        font-weight: 500;
    }
    .health-card h4 {
        color: #2c3e50;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }
    .health-card p {
        color: #2c3e50;
        margin: 0;
        font-weight: 500;
    }
    .analysis-section h3 {
        color: #2c3e50 !important;
        font-weight: 600;
    }
    .treatment-section h4 {
        color: #2c3e50 !important;
        font-weight: 600;
    }
    .treatment-section p {
        color: #2c3e50 !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'doctor' not in st.session_state:
    st.session_state.doctor = None
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []

def load_model():
    """Load the Smart Plant Doctor model"""
    if st.session_state.doctor is None:
        try:
            with st.spinner("🌱 Loading Smart Plant Doctor model..."):
                model_path = os.path.join(project_root, "ai", "exports", "smart_plant_doctor_model.pth")
                st.session_state.doctor = SmartPlantDoctor(model_path=model_path)
            st.success("✅ Model loaded successfully!")
        except Exception as e:
            st.error(f"❌ Error loading model: {str(e)}")
            return False
    return True

def generate_mock_sensor_data():
    """Generate mock sensor data for demonstration"""
    now = datetime.now()
    data = {
        'timestamp': now,
        'temperature': round(random.uniform(20, 30), 1),
        'humidity': round(random.uniform(40, 80), 1),
        'light': round(random.uniform(200, 1000), 0),
        'soil_moisture': round(random.uniform(30, 70), 1),
        'ph': round(random.uniform(6.0, 7.5), 1),
        'nutrients': round(random.uniform(60, 90), 1)
    }
    return data

def check_alerts_for_plant(plant_name: str, sensor_data: dict):
    """Check for alerts based on sensor data for a specific plant"""
    # Convert sensor data to the format expected by alert system
    alert_sensor_data = {
        'soil_moisture': sensor_data['soil_moisture'],
        'temperature': sensor_data['temperature'],
        'humidity': sensor_data['humidity'],
        'sunlight': sensor_data['light'] / 100  # Convert to hours (simplified)
    }
    
    # Check for alerts
    new_alerts = alert_system.check_sensor_data(plant_name, alert_sensor_data)
    return new_alerts

def get_sensor_history(plant: str, limit: int = 500):
    """Get historical sensor data for a plant from DB; fallback to mock if DB missing.

    Note: The ingest stores `ts` from the device; we use row order for recency
    and synthesize timestamps spaced uniformly for charting.
    """
    # Try DB-backed history first for true realtime charts.
    if _db_exists() and plant:
        con = sqlite3.connect(DB_PATH)
        try:
            rows = con.execute(
                "SELECT ts, temperature, humidity, light, soil_moisture FROM readings WHERE plant=? ORDER BY rowid DESC LIMIT ?",
                (plant, limit),
            ).fetchall()
            if rows:
                rows = list(reversed(rows))
                data_points = []
                for idx, r in enumerate(rows):
                    data_points.append({
                        'timestamp': _parse_ts_to_datetime(r[0], fallback_index=len(rows) - idx),
                        'temperature': float(r[1]),
                        'humidity': float(r[2]),
                        'light': float(r[3]),
                        'soil_moisture': float(r[4]),
                    })
                return pd.DataFrame(data_points)
        except Exception:
            pass
        finally:
            con.close()

    # Fallback mock data when DB is unavailable/empty.
    base_time = datetime.now() - timedelta(hours=24)
    hours = 24
    data_points = []
    
    # Base values for realistic plant environment
    base_temp = 22
    base_humidity = 60
    base_light = 500
    base_soil = 45
    
    for i in range(hours):
        # Create realistic daily patterns
        hour_of_day = (base_time + timedelta(hours=i)).hour
        
        # Temperature: cooler at night, warmer during day
        if 6 <= hour_of_day <= 18:
            temp_variation = 3 * np.sin((hour_of_day - 6) * np.pi / 12)
        else:
            temp_variation = -2
        temperature = base_temp + temp_variation + random.uniform(-1, 1)
        
        # Humidity: higher at night, lower during day
        if 6 <= hour_of_day <= 18:
            humidity_variation = 10 * np.cos((hour_of_day - 6) * np.pi / 12)
        else:
            humidity_variation = 5
        humidity = base_humidity + humidity_variation + random.uniform(-3, 3)
        
        # Light: zero at night, peak during midday
        if 6 <= hour_of_day <= 18:
            light_variation = 300 * np.sin((hour_of_day - 6) * np.pi / 12)
            light = light_variation + random.uniform(-50, 50)
        else:
            light = random.uniform(0, 20)  # Very low at night
        
        # Soil moisture: gradual decrease, occasional spikes (watering)
        soil_trend = -0.5 * i  # Gradual decrease over time
        soil_spike = 15 if random.random() < 0.1 else 0  # 10% chance of watering spike
        soil_moisture = base_soil + soil_trend + soil_spike + random.uniform(-2, 2)
        soil_moisture = max(20, min(80, soil_moisture))  # Keep within realistic bounds
        
        data_points.append({
            'timestamp': base_time + timedelta(hours=i),
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'light': round(max(0, light), 0),
            'soil_moisture': round(soil_moisture, 1)
        })
    
    return pd.DataFrame(data_points)

def home_dashboard():
    """Home page with sensor data dashboard"""
    st.markdown('<h1 class="main-header">🌱 Smart Plant Doctor Dashboard</h1>', unsafe_allow_html=True)
    
    st.subheader("📊 Real-time Plant Monitoring")
    # If live DB exists, offer plant/device dropdown and use live reading
    live_mode = _db_exists()
    selected_plant = None
    current_data = None
    previous_data = None
    if live_mode:
        plants = get_plants_from_db()
        if plants:
            selected_plant = st.selectbox("Select plant/device", plants)
            live = get_latest_from_db(selected_plant)
            previous_data = get_previous_from_db(selected_plant)
            if live:
                current_data = {
                    'temperature': round(float(live['temperature']), 1),
                    'humidity': round(float(live['humidity']), 1),
                    'light': round(float(live['light']), 0),
                    'soil_moisture': round(float(live['soil_moisture']), 1),
                    'timestamp': _parse_ts_to_datetime(live['ts'])
                }
    
    # Fallback to mock data if no live reading
    if current_data is None:
        current_data = generate_mock_sensor_data()
    
    # Tag showing source
    if live_mode and selected_plant:
        st.caption(f"Live data from sensors DB — plant: {selected_plant}")
    else:
        st.caption("Demo data (no live sensors DB found)")
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp_change = random.uniform(-2, 2)
        if previous_data is not None:
            temp_change = current_data['temperature'] - float(previous_data['temperature'])
        temp_color = "normal"
        if current_data['temperature'] < 18 or current_data['temperature'] > 28:
            temp_color = "inverse"
        st.metric(
            "🌡️ Temperature", 
            f"{current_data['temperature']}°C", 
            f"{temp_change:+.1f}°C",
            delta_color=temp_color
        )
    
    with col2:
        humidity_change = random.uniform(-5, 5)
        if previous_data is not None:
            humidity_change = current_data['humidity'] - float(previous_data['humidity'])
        humidity_color = "normal"
        if current_data['humidity'] < 40 or current_data['humidity'] > 80:
            humidity_color = "inverse"
        st.metric(
            "💧 Humidity", 
            f"{current_data['humidity']}%", 
            f"{humidity_change:+.1f}%",
            delta_color=humidity_color
        )
    
    with col3:
        light_change = random.uniform(-50, 50)
        if previous_data is not None:
            light_change = current_data['light'] - float(previous_data['light'])
        light_color = "normal"
        if current_data['light'] < 200 or current_data['light'] > 1000:
            light_color = "inverse"
        st.metric(
            "🌞 Light Intensity", 
            f"{current_data['light']} lux", 
            f"{light_change:+.0f} lux",
            delta_color=light_color
        )
    
    with col4:
        moisture_change = random.uniform(-3, 3)
        if previous_data is not None:
            moisture_change = current_data['soil_moisture'] - float(previous_data['soil_moisture'])
        moisture_color = "normal"
        if current_data['soil_moisture'] < 30 or current_data['soil_moisture'] > 70:
            moisture_color = "inverse"
        st.metric(
            "🌱 Soil Moisture", 
            f"{current_data['soil_moisture']}%", 
            f"{moisture_change:+.1f}%",
            delta_color=moisture_color
        )
        soil_label, soil_color, soil_icon = get_soil_condition(float(current_data['soil_moisture']))
        st.markdown(
            f"<p style='margin-top:0.25rem; font-weight:600; color:{soil_color};'>{soil_icon} Soil Status: {soil_label}</p>",
            unsafe_allow_html=True,
        )
    
    # Additional metrics (health only)
    col7, = st.columns(1)
    
    with col7:
        health_score = calculate_health_score(current_data)
        health_color = "normal"
        if health_score < 80:
            health_color = "inverse"
        st.metric("💚 Plant Health", f"{health_score}%", "5%", delta_color=health_color)
    
    # Charts section
    st.subheader("📈 Historical Data (Last 24 Hours)")
    
    # Get historical data from DB for selected plant when available
    df = get_sensor_history(selected_plant) if (live_mode and selected_plant) else get_sensor_history("Demo")
    
    # Temperature and Humidity chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig_temp = px.line(
            df, x='timestamp', y='temperature',
            title='🌡️ Temperature Over Time',
            labels={'temperature': 'Temperature (°C)', 'timestamp': 'Time'}
        )
        fig_temp.add_hline(y=22, line_dash="dash", line_color="green", 
                          annotation_text="Ideal: 22°C", annotation_position="top right")
        fig_temp.update_layout(height=300)
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        fig_humidity = px.line(
            df, x='timestamp', y='humidity',
            title='💧 Humidity Over Time',
            labels={'humidity': 'Humidity (%)', 'timestamp': 'Time'}
        )
        fig_humidity.add_hline(y=60, line_dash="dash", line_color="green",
                              annotation_text="Ideal: 60%", annotation_position="top right")
        fig_humidity.update_layout(height=300)
        st.plotly_chart(fig_humidity, use_container_width=True)
    
    # Light and Soil Moisture chart
    col3, col4 = st.columns(2)
    
    with col3:
        fig_light = px.line(
            df, x='timestamp', y='light',
            title='🌞 Light Intensity Over Time',
            labels={'light': 'Light (lux)', 'timestamp': 'Time'}
        )
        fig_light.add_hline(y=500, line_dash="dash", line_color="green",
                           annotation_text="Ideal: 500 lux", annotation_position="top right")
        fig_light.update_layout(height=300)
        st.plotly_chart(fig_light, use_container_width=True)
    
    with col4:
        fig_moisture = px.line(
            df, x='timestamp', y='soil_moisture',
            title='🌱 Soil Moisture Over Time',
            labels={'soil_moisture': 'Moisture (%)', 'timestamp': 'Time'}
        )
        fig_moisture.add_hline(y=45, line_dash="dash", line_color="green",
                              annotation_text="Ideal: 45%", annotation_position="top right")
        fig_moisture.update_layout(height=300)
        st.plotly_chart(fig_moisture, use_container_width=True)
    
    # Plant Health Status
    st.subheader("🌿 Plant Health Status")
    
    health_col1, health_col2, health_col3 = st.columns(3)
    
    with health_col1:
        if health_score >= 85:
            status_color = "#d4edda"
            text_color = "#155724"
            status_text = "✅ Excellent"
        elif health_score >= 70:
            status_color = "#fff3cd"
            text_color = "#856404"
            status_text = "⚠️ Good"
        else:
            status_color = "#f8d7da"
            text_color = "#721c24"
            status_text = "❌ Needs Attention"
        
        st.markdown(f"""
        <div style="background-color: {status_color}; padding: 1rem; border-radius: 10px; border-left: 5px solid #2E8B57; color: {text_color};">
            <h4 style="color: {text_color}; margin: 0 0 0.5rem 0;">{status_text}</h4>
            <p style="color: {text_color}; margin: 0; font-weight: 600;">Overall Health Score: {health_score}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with health_col2:
        recommendations = []
        if current_data['soil_moisture'] < 30:
            recommendations.append("💧 Water your plant")
        if current_data['light'] < 300:
            recommendations.append("🌞 Increase light exposure")
        if current_data['temperature'] > 28:
            recommendations.append("❄️ Provide shade")
        if current_data['humidity'] < 40:
            recommendations.append("💨 Increase humidity")
        
        if not recommendations:
            recommendations.append("✅ All conditions optimal")
        
        rec_text = "<br>".join(recommendations)
        st.markdown(f"""
        <div style="background-color: #e8f5e8; padding: 1rem; border-radius: 10px; border-left: 5px solid #2E8B57; color: #2c3e50;">
            <h4 style="color: #2c3e50; margin: 0 0 0.5rem 0; font-weight: 600;">💡 Recommendations</h4>
            <p style="color: #2c3e50; margin: 0; font-weight: 500;">{rec_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with health_col3:
        next_check = datetime.now() + timedelta(hours=6)
        st.markdown(f"""
        <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 10px; border-left: 5px solid #2E8B57; color: #2c3e50;">
            <h4 style="color: #2c3e50; margin: 0 0 0.5rem 0; font-weight: 600;">📅 Next Check</h4>
            <p style="color: #2c3e50; margin: 0; font-weight: 500;">{next_check.strftime('%H:%M')} today</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Alerts section
    st.markdown("---")
    st.subheader("🚨 Plant Alerts")
    
    # Check for alerts with current sensor data
    plant_name = "Rose"  # Default plant for demo
    new_alerts = check_alerts_for_plant(plant_name, current_data)
    
    # Get all active alerts
    active_alerts = alert_system.get_active_alerts()
    
    if active_alerts:
        # Display alerts by severity
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            severity_alerts = [a for a in active_alerts if a.severity == severity]
            if severity_alerts:
                alert_config = ALERT_LEVELS[severity]
                st.markdown(f"""
                <div style="background-color: {alert_config['color']}; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 5px solid #dc3545;">
                    <h4 style="color: #721c24; margin: 0 0 0.5rem 0; font-weight: 600;">{alert_config['icon']} {severity} Alerts ({len(severity_alerts)})</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for alert in severity_alerts:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 0.75rem; border-radius: 5px; margin: 0.25rem 0; border-left: 3px solid #dc3545;">
                            <p style="color: #2c3e50; margin: 0; font-weight: 500;">{alert.message}</p>
                            <small style="color: #6c757d;">{alert.timestamp.strftime('%H:%M:%S')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("✓", key=f"ack_{alert.id}", help="Acknowledge"):
                            alert_system.acknowledge_alert(alert.id)
                            st.rerun()
                    with col3:
                        if st.button("✕", key=f"dismiss_{alert.id}", help="Dismiss"):
                            alert_system.dismiss_alert(alert.id)
                            st.rerun()
        
        # Alert management buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔕 Dismiss All", use_container_width=True):
                dismissed_count = alert_system.dismiss_all_alerts()
                st.success(f"Dismissed {dismissed_count} alerts")
                st.rerun()
        with col2:
            if st.button("📊 Alert Summary", use_container_width=True):
                summary = alert_system.get_alert_summary()
                st.json(summary)
        with col3:
            if st.button("🧹 Cleanup Old", use_container_width=True):
                alert_system.cleanup_old_alerts(hours=1)
                st.success("Cleaned up old alerts")
                st.rerun()
    else:
        st.success("✅ No active alerts - All plants are healthy!")
    
    # Auto-refresh button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Optional auto-refresh for near realtime dashboard updates.
    auto_refresh = st.sidebar.checkbox("Auto-refresh dashboard", value=True)
    refresh_seconds = st.sidebar.slider("Refresh interval (seconds)", min_value=2, max_value=30, value=5)
    if auto_refresh:
        if AUTOREFRESH_COMPONENT_AVAILABLE:
            st_autorefresh(interval=refresh_seconds * 1000, key="dashboard_autorefresh")
        else:
            st.caption("Tip: install streamlit-autorefresh for smoother non-blocking updates.")
            time.sleep(refresh_seconds)
            st.rerun()

def disease_detection():
    """Disease detection page"""
    st.markdown('<h1 class="main-header">🔬 Plant Disease Detection</h1>', unsafe_allow_html=True)
    
    # Load model
    if not load_model():
        return
    
    st.subheader("📸 Upload Plant Image")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image of your plant",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of the plant leaves or affected area"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📷 Uploaded Image")
            image = Image.open(uploaded_file)
            st.image(image, caption="Your plant image", use_container_width=True)
        
        with col2:
            st.markdown("### 🔍 Analysis Results")
            
            # Make prediction
            with st.spinner("🔬 Analyzing plant image..."):
                try:
                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Get prediction
                    result = st.session_state.doctor.predict(temp_path)
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    if 'error' in result:
                        st.markdown(f"""
                        <div class="error-message">
                            <h4>❌ Error</h4>
                            <p>{result['error']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Display results
                        confidence_color = "#d4edda" if result['confidence'] > 80 else "#fff3cd" if result['confidence'] > 60 else "#f8d7da"
                        text_color = "#155724" if result['confidence'] > 80 else "#856404" if result['confidence'] > 60 else "#721c24"
                        st.markdown(f"""
                        <div style="background-color: {confidence_color}; padding: 1rem; border-radius: 5px; border: 1px solid #c3e6cb; color: {text_color};">
                            <h3 style="color: {text_color}; margin: 0 0 0.5rem 0;">🎯 {result['output_format']}</h3>
                            <p style="color: {text_color}; margin: 0.25rem 0;"><strong>Confidence:</strong> {result['confidence']:.2f}%</p>
                            <p style="color: {text_color}; margin: 0.25rem 0;"><strong>Class:</strong> {result['class_name']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Treatment recommendations
                        if result['treatment']:
                            treatment = result['treatment']
                            
                            st.markdown("### 🩺 Treatment Recommendations")
                            
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 5px solid #2E8B57; color: #2c3e50;">
                                <h4 style="color: #2c3e50; margin: 0 0 0.5rem 0; font-weight: 600;">📋 Disease: {treatment['name']}</h4>
                                <p style="color: #2c3e50; margin: 0; font-weight: 500;"><strong>🔍 Symptoms:</strong> {treatment['symptoms']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("#### 💊 Home Remedies:")
                            for i, remedy in enumerate(treatment['home_remedies'], 1):
                                st.markdown(f"**{i}.** {remedy}")
                            
                            st.markdown(f"""
                            <div style="background-color: #e8f5e8; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 5px solid #2E8B57; color: #2c3e50;">
                                <h4 style="color: #2c3e50; margin: 0 0 0.5rem 0; font-weight: 600;">🛡️ Prevention</h4>
                                <p style="color: #2c3e50; margin: 0; font-weight: 500;">{treatment['prevention']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-message">
                        <h4>❌ Error</h4>
                        <p>Error processing image: {str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # Show example images and instructions
        st.info("👆 Please upload an image to get started with disease detection")
        
        st.subheader("📋 How to Use:")
        st.markdown("""
        1. **Take a clear photo** of your plant's leaves or affected area
        2. **Upload the image** using the file uploader above
        3. **Wait for analysis** - our AI will identify the disease
        4. **Follow treatment recommendations** for plant recovery
        
        **💡 Tips for better results:**
        - Use good lighting
        - Focus on the affected leaves
        - Avoid blurry or dark images
        - Include multiple leaves if possible
        """)
        
        # Show supported plants
        st.subheader("🌱 Supported Plants:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🌿 Aloe Vera**
            - Anthracnose
            - Leaf Spot
            - Rust
            - Sunburn
            - Healthy
            """)
        
        with col2:
            st.markdown("""
            **🌹 Rose**
            - Black Spot
            - Powdery Mildew
            - Rust
            - Mosaic Virus
            - Downy Mildew
            - Insect Damage
            - Healthy
            """)
        
        with col3:
            st.markdown("""
            **🌺 Hibiscus**
            - Blight
            - Necrosis
            - Scorch
            - Healthy
            """)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.markdown("""
            **🌼 Chrysanthemum**
            - Bacterial Leaf Spot
            - Septoria Leaf Spot
            - Healthy
            """)
        
        with col5:
            st.markdown("""
            **🌿 Money Plant**
            - Bacterial Wilt
            - Chlorosis
            - Manganese Toxicity
            - Healthy
            """)
        
        with col6:
            st.markdown("""
            **🌾 Turmeric**
            - Aphid Infestation
            - Leaf Blotch
            - Leaf Necrosis
            - Leaf Spot
            - Healthy
            """)

def about_page():
    """About page"""
    st.markdown('<h1 class="main-header">ℹ️ About Smart Plant Doctor</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## 🌱 What is Smart Plant Doctor?
    
    Smart Plant Doctor is an AI-powered plant care system that combines:
    - **Real-time sensor monitoring** of plant health parameters
    - **Computer vision** for disease detection and diagnosis
    - **Expert treatment recommendations** for plant recovery
    
    ## 🔬 How It Works
    
    ### Sensor Monitoring
    - Continuously tracks temperature, humidity, light, and soil moisture
    - Provides real-time alerts and recommendations
    - Historical data analysis for trend identification
    
    ### Disease Detection
    - Uses advanced MobileNetV2 deep learning model
    - Trained on 29 different plant disease classes
    - 92.37% accuracy in disease identification
    - Provides detailed treatment recommendations
    
    ## 🌿 Supported Plants
    
    Our AI model can identify diseases in:
    - **Aloe Vera** (5 disease types)
    - **Chrysanthemum** (3 disease types)
    - **Hibiscus** (4 disease types)
    - **Money Plant** (4 disease types)
    - **Rose** (8 disease types)
    - **Turmeric** (5 disease types)
    
    ## 🛠️ Technology Stack
    
    - **AI Model**: PyTorch + MobileNetV2
    - **Web Interface**: Streamlit
    - **Data Visualization**: Plotly
    - **Image Processing**: PIL/Pillow
    
    ## 📊 Model Performance
    
    - **Accuracy**: 92.37%
    - **Classes**: 29 plant disease classes
    - **Input Size**: 224x224 pixels
    - **Training Data**: 45,895+ plant images
    
    ## 🚀 Features
    
    ### Real-time Monitoring
    - Live sensor data visualization
    - Historical trend analysis
    - Health score calculation
    - Automated recommendations
    
    ### Disease Detection
    - Instant image analysis
    - High-accuracy predictions
    - Detailed treatment plans
    - Prevention strategies
    
    ## 📞 Support
    
    For technical support or questions, please contact our team.
    """)

def alerts_page():
    """Dedicated alerts management page"""
    st.markdown('<h1 class="main-header">🚨 Plant Alerts Management</h1>', unsafe_allow_html=True)
    
    # Alert summary
    summary = alert_system.get_alert_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Active Alerts", summary["total_active"])
    with col2:
        st.metric("Critical Alerts", summary["by_severity"]["CRITICAL"])
    with col3:
        st.metric("High Priority", summary["by_severity"]["HIGH"])
    with col4:
        st.metric("Medium Priority", summary["by_severity"]["MEDIUM"])
    
    st.markdown("---")
    
    # Alert management controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Alerts", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🔕 Dismiss All", use_container_width=True):
            dismissed_count = alert_system.dismiss_all_alerts()
            st.success(f"Dismissed {dismissed_count} alerts")
            st.rerun()
    
    with col3:
        if st.button("🧹 Cleanup Old", use_container_width=True):
            alert_system.cleanup_old_alerts(hours=1)
            st.success("Cleaned up old alerts")
            st.rerun()
    
    with col4:
        if st.button("📊 Export Alerts", use_container_width=True):
            # Export alerts as JSON
            alerts_data = []
            for alert in alert_system.alert_history:
                alerts_data.append({
                    "id": alert.id,
                    "plant_name": alert.plant_name,
                    "sensor_type": alert.sensor_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "is_active": alert.is_active,
                    "is_acknowledged": alert.is_acknowledged
                })
            
            st.download_button(
                label="📥 Download Alerts JSON",
                data=pd.DataFrame(alerts_data).to_csv(index=False),
                file_name=f"plant_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    st.markdown("---")
    
    # Display all alerts
    active_alerts = alert_system.get_active_alerts()
    
    if active_alerts:
        st.subheader("📋 Active Alerts")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severity_filter = st.selectbox(
                "Filter by Severity",
                ["All"] + list(ALERT_LEVELS.keys()),
                key="severity_filter"
            )
        
        with col2:
            plant_filter = st.selectbox(
                "Filter by Plant",
                ["All"] + list(set(alert.plant_name for alert in active_alerts)),
                key="plant_filter"
            )
        
        with col3:
            sensor_filter = st.selectbox(
                "Filter by Sensor",
                ["All"] + list(set(alert.sensor_type for alert in active_alerts)),
                key="sensor_filter"
            )
        
        # Apply filters
        filtered_alerts = active_alerts
        
        if severity_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity_filter]
        
        if plant_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.plant_name == plant_filter]
        
        if sensor_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.sensor_type == sensor_filter]
        
        # Display filtered alerts
        if filtered_alerts:
            for alert in filtered_alerts:
                alert_config = ALERT_LEVELS[alert.severity]
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="background-color: {alert_config['color']}; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 5px solid #dc3545;">
                            <h4 style="color: #721c24; margin: 0 0 0.5rem 0; font-weight: 600;">
                                {alert_config['icon']} {alert.severity} - {alert.plant_name}
                            </h4>
                            <p style="color: #2c3e50; margin: 0.25rem 0; font-weight: 500;">{alert.message}</p>
                            <small style="color: #6c757d;">
                                Sensor: {alert.sensor_type} | 
                                Value: {alert.current_value} | 
                                Threshold: {alert.threshold_value} | 
                                Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("✓", key=f"ack_{alert.id}", help="Acknowledge"):
                            alert_system.acknowledge_alert(alert.id)
                            st.rerun()
                    
                    with col3:
                        if st.button("✕", key=f"dismiss_{alert.id}", help="Dismiss"):
                            alert_system.dismiss_alert(alert.id)
                            st.rerun()
                    
                    with col4:
                        if st.button("ℹ️", key=f"info_{alert.id}", help="More Info"):
                            st.info(f"""
                            **Alert Details:**
                            - ID: {alert.id}
                            - Plant: {alert.plant_name}
                            - Sensor: {alert.sensor_type}
                            - Current Value: {alert.current_value}
                            - Threshold: {alert.threshold_value}
                            - Severity: {alert.severity}
                            - Created: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                            - Acknowledged: {'Yes' if alert.is_acknowledged else 'No'}
                            """)
        else:
            st.info("No alerts match the selected filters.")
    else:
        st.success("✅ No active alerts - All plants are healthy!")
    
    # Alert history
    st.markdown("---")
    st.subheader("📈 Alert History")
    
    if alert_system.alert_history:
        # Create a DataFrame for better display
        history_data = []
        for alert in alert_system.alert_history[-50:]:  # Show last 50 alerts
            history_data.append({
                "Timestamp": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "Plant": alert.plant_name,
                "Sensor": alert.sensor_type,
                "Severity": alert.severity,
                "Message": alert.message,
                "Status": "Active" if alert.is_active else "Dismissed",
                "Acknowledged": "Yes" if alert.is_acknowledged else "No"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No alert history available.")

def main():
    """Main application"""
    # Sidebar navigation
    st.sidebar.title("🌱 Smart Plant Doctor")
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox(
        "Navigate",
        ["🏠 Home Dashboard", "🔬 Disease Detection", "🚨 Alerts", "ℹ️ About"]
    )
    
    st.sidebar.markdown("---")
    
    # Model status
    if st.session_state.doctor:
        st.sidebar.success("✅ AI Model Loaded")
    else:
        st.sidebar.info("🔄 AI Model Not Loaded")
    
    # Quick stats
    st.sidebar.markdown("### 📊 Quick Stats")
    st.sidebar.metric("Model Accuracy", "92.37%")
    st.sidebar.metric("Supported Plants", "6")
    st.sidebar.metric("Disease Classes", "29")
    
    # Page routing
    if page == "🏠 Home Dashboard":
        home_dashboard()
    elif page == "🔬 Disease Detection":
        disease_detection()
    elif page == "🚨 Alerts":
        alerts_page()
    elif page == "ℹ️ About":
        about_page()

if __name__ == "__main__":
    main()
