#!/usr/bin/env python3
"""
Demo script to test the alert system functionality
"""

import streamlit as st
import random
from datetime import datetime
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.alert_system import alert_system, Alert
from alert_config import ALERT_LEVELS, PLANT_THRESHOLDS

st.title("🚨 Smart Plant Doctor - Alert System Demo")

st.markdown("""
This demo shows how the alert system works with different sensor data scenarios.
The system monitors plant sensor data and generates alerts when values go outside optimal ranges.
""")

# Demo controls
col1, col2 = st.columns(2)

with col1:
    plant_name = st.selectbox(
        "Select Plant",
        list(PLANT_THRESHOLDS.keys()),
        help="Different plants have different optimal sensor ranges"
    )

with col2:
    scenario = st.selectbox(
        "Select Scenario",
        [
            "Normal Conditions",
            "Low Soil Moisture",
            "High Temperature", 
            "Low Humidity",
            "Too Much Sunlight",
            "Critical Conditions"
        ],
        help="Choose a scenario to see how alerts are generated"
    )

# Generate sensor data based on scenario
def generate_scenario_data(plant_name, scenario):
    thresholds = PLANT_THRESHOLDS[plant_name]
    
    if scenario == "Normal Conditions":
        return {
            'soil_moisture': thresholds['soil_moisture']['ideal'],
            'temperature': thresholds['temperature']['ideal'],
            'humidity': thresholds['humidity']['ideal'],
            'sunlight': thresholds['sunlight']['ideal']
        }
    elif scenario == "Low Soil Moisture":
        return {
            'soil_moisture': thresholds['soil_moisture']['min'] - 10,
            'temperature': thresholds['temperature']['ideal'],
            'humidity': thresholds['humidity']['ideal'],
            'sunlight': thresholds['sunlight']['ideal']
        }
    elif scenario == "High Temperature":
        return {
            'soil_moisture': thresholds['soil_moisture']['ideal'],
            'temperature': thresholds['temperature']['max'] + 5,
            'humidity': thresholds['humidity']['ideal'],
            'sunlight': thresholds['sunlight']['ideal']
        }
    elif scenario == "Low Humidity":
        return {
            'soil_moisture': thresholds['soil_moisture']['ideal'],
            'temperature': thresholds['temperature']['ideal'],
            'humidity': thresholds['humidity']['min'] - 15,
            'sunlight': thresholds['sunlight']['ideal']
        }
    elif scenario == "Too Much Sunlight":
        return {
            'soil_moisture': thresholds['soil_moisture']['ideal'],
            'temperature': thresholds['temperature']['ideal'],
            'humidity': thresholds['humidity']['ideal'],
            'sunlight': thresholds['sunlight']['max'] + 2
        }
    elif scenario == "Critical Conditions":
        return {
            'soil_moisture': thresholds['soil_moisture']['min'] - 20,
            'temperature': thresholds['temperature']['max'] + 10,
            'humidity': thresholds['humidity']['min'] - 25,
            'sunlight': thresholds['sunlight']['max'] + 3
        }

# Generate and display sensor data
sensor_data = generate_scenario_data(plant_name, scenario)

st.markdown("### 📊 Current Sensor Data")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Soil Moisture", f"{sensor_data['soil_moisture']}%")
with col2:
    st.metric("Temperature", f"{sensor_data['temperature']}°C")
with col3:
    st.metric("Humidity", f"{sensor_data['humidity']}%")
with col4:
    st.metric("Sunlight", f"{sensor_data['sunlight']} hours")

# Show plant thresholds
st.markdown("### 📋 Plant Thresholds")
thresholds = PLANT_THRESHOLDS[plant_name]

threshold_data = {
    "Sensor": ["Soil Moisture", "Temperature", "Humidity", "Sunlight"],
    "Min": [
        f"{thresholds['soil_moisture']['min']}%",
        f"{thresholds['temperature']['min']}°C", 
        f"{thresholds['humidity']['min']}%",
        f"{thresholds['sunlight']['min']} hours"
    ],
    "Ideal": [
        f"{thresholds['soil_moisture']['ideal']}%",
        f"{thresholds['temperature']['ideal']}°C",
        f"{thresholds['humidity']['ideal']}%", 
        f"{thresholds['sunlight']['ideal']} hours"
    ],
    "Max": [
        f"{thresholds['soil_moisture']['max']}%",
        f"{thresholds['temperature']['max']}°C",
        f"{thresholds['humidity']['max']}%",
        f"{thresholds['sunlight']['max']} hours"
    ]
}

st.table(threshold_data)

# Check for alerts
if st.button("🔍 Check for Alerts", type="primary"):
    with st.spinner("Checking sensor data for alerts..."):
        new_alerts = alert_system.check_sensor_data(plant_name, sensor_data)
        
        if new_alerts:
            st.markdown("### 🚨 Generated Alerts")
            
            for alert in new_alerts:
                alert_config = ALERT_LEVELS[alert.severity]
                st.markdown(f"""
                <div style="background-color: {alert_config['color']}; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 5px solid #dc3545;">
                    <h4 style="color: #721c24; margin: 0 0 0.5rem 0; font-weight: 600;">
                        {alert_config['icon']} {alert.severity} Alert
                    </h4>
                    <p style="color: #2c3e50; margin: 0.25rem 0; font-weight: 500;">{alert.message}</p>
                    <small style="color: #6c757d;">
                        Sensor: {alert.sensor_type} | 
                        Current: {alert.current_value} | 
                        Threshold: {alert.threshold_value}
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No alerts generated - All sensor values are within optimal ranges!")

# Show active alerts
active_alerts = alert_system.get_active_alerts()

if active_alerts:
    st.markdown("### 📋 Active Alerts")
    
    for alert in active_alerts:
        alert_config = ALERT_LEVELS[alert.severity]
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background-color: {alert_config['color']}; padding: 0.75rem; border-radius: 5px; margin: 0.25rem 0; border-left: 3px solid #dc3545;">
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

# Alert management
st.markdown("### 🛠️ Alert Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔕 Dismiss All Alerts"):
        dismissed_count = alert_system.dismiss_all_alerts()
        st.success(f"Dismissed {dismissed_count} alerts")
        st.rerun()

with col2:
    if st.button("📊 Show Alert Summary"):
        summary = alert_system.get_alert_summary()
        st.json(summary)

with col3:
    if st.button("🧹 Cleanup Old Alerts"):
        alert_system.cleanup_old_alerts(hours=1)
        st.success("Cleaned up old alerts")
        st.rerun()

# Alert statistics
if alert_system.alert_history:
    st.markdown("### 📈 Alert Statistics")
    
    total_alerts = len(alert_system.alert_history)
    active_count = len(active_alerts)
    acknowledged_count = len([a for a in alert_system.alert_history if a.is_acknowledged])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Alerts", total_alerts)
    with col2:
        st.metric("Active Alerts", active_count)
    with col3:
        st.metric("Acknowledged", acknowledged_count)

st.markdown("---")
st.info("""
**How the Alert System Works:**

1. **Threshold Monitoring**: Each plant has specific optimal ranges for soil moisture, temperature, humidity, and sunlight
2. **Severity Calculation**: Alerts are classified as LOW, MEDIUM, HIGH, or CRITICAL based on how far values deviate from ideal
3. **Rate Limiting**: Prevents spam by limiting alerts per hour and implementing cooldown periods
4. **Alert Management**: Users can acknowledge, dismiss, and filter alerts
5. **History Tracking**: All alerts are logged for analysis and reporting

**Future Enhancements:**
- WhatsApp notifications
- Email alerts
- Mobile push notifications
- Custom alert thresholds per plant
""")
