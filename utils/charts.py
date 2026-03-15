"""
Chart utilities for Smart Plant Doctor Streamlit App
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

def create_temperature_chart(df: pd.DataFrame, ideal_temp: float = 22) -> go.Figure:
    """
    Create temperature chart with ideal range
    
    Args:
        df: DataFrame with timestamp and temperature columns
        ideal_temp: Ideal temperature value
        
    Returns:
        Plotly figure
    """
    fig = px.line(
        df, 
        x='timestamp', 
        y='temperature',
        title='🌡️ Temperature Over Time',
        labels={'temperature': 'Temperature (°C)', 'timestamp': 'Time'},
        color_discrete_sequence=['#2E8B57']
    )
    
    # Add ideal temperature line
    fig.add_hline(
        y=ideal_temp, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Ideal: {ideal_temp}°C", 
        annotation_position="top right"
    )
    
    # Add temperature range
    fig.add_hline(y=ideal_temp + 5, line_dash="dot", line_color="orange", opacity=0.5)
    fig.add_hline(y=ideal_temp - 5, line_dash="dot", line_color="orange", opacity=0.5)
    
    fig.update_layout(
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_humidity_chart(df: pd.DataFrame, ideal_humidity: float = 60) -> go.Figure:
    """
    Create humidity chart with ideal range
    
    Args:
        df: DataFrame with timestamp and humidity columns
        ideal_humidity: Ideal humidity value
        
    Returns:
        Plotly figure
    """
    fig = px.line(
        df, 
        x='timestamp', 
        y='humidity',
        title='💧 Humidity Over Time',
        labels={'humidity': 'Humidity (%)', 'timestamp': 'Time'},
        color_discrete_sequence=['#4ECDC4']
    )
    
    # Add ideal humidity line
    fig.add_hline(
        y=ideal_humidity, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Ideal: {ideal_humidity}%", 
        annotation_position="top right"
    )
    
    # Add humidity range
    fig.add_hline(y=ideal_humidity + 15, line_dash="dot", line_color="orange", opacity=0.5)
    fig.add_hline(y=ideal_humidity - 15, line_dash="dot", line_color="orange", opacity=0.5)
    
    fig.update_layout(
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_light_chart(df: pd.DataFrame, ideal_light: float = 500) -> go.Figure:
    """
    Create light intensity chart with ideal range
    
    Args:
        df: DataFrame with timestamp and light columns
        ideal_light: Ideal light value
        
    Returns:
        Plotly figure
    """
    fig = px.line(
        df, 
        x='timestamp', 
        y='light',
        title='🌞 Light Intensity Over Time',
        labels={'light': 'Light (lux)', 'timestamp': 'Time'},
        color_discrete_sequence=['#FFE66D']
    )
    
    # Add ideal light line
    fig.add_hline(
        y=ideal_light, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Ideal: {ideal_light} lux", 
        annotation_position="top right"
    )
    
    # Add light range
    fig.add_hline(y=ideal_light + 200, line_dash="dot", line_color="orange", opacity=0.5)
    fig.add_hline(y=ideal_light - 200, line_dash="dot", line_color="orange", opacity=0.5)
    
    fig.update_layout(
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_moisture_chart(df: pd.DataFrame, ideal_moisture: float = 45) -> go.Figure:
    """
    Create soil moisture chart with ideal range
    
    Args:
        df: DataFrame with timestamp and soil_moisture columns
        ideal_moisture: Ideal moisture value
        
    Returns:
        Plotly figure
    """
    fig = px.line(
        df, 
        x='timestamp', 
        y='soil_moisture',
        title='🌱 Soil Moisture Over Time',
        labels={'soil_moisture': 'Moisture (%)', 'timestamp': 'Time'},
        color_discrete_sequence=['#8B4513']
    )
    
    # Add ideal moisture line
    fig.add_hline(
        y=ideal_moisture, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Ideal: {ideal_moisture}%", 
        annotation_position="top right"
    )
    
    # Add moisture range
    fig.add_hline(y=ideal_moisture + 15, line_dash="dot", line_color="orange", opacity=0.5)
    fig.add_hline(y=ideal_moisture - 15, line_dash="dot", line_color="orange", opacity=0.5)
    
    fig.update_layout(
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_combined_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create combined chart with all sensor data
    
    Args:
        df: DataFrame with all sensor columns
        
    Returns:
        Plotly figure with subplots
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Temperature', 'Humidity', 'Light Intensity', 'Soil Moisture'),
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # Temperature
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['temperature'], name='Temperature', line=dict(color='#2E8B57')),
        row=1, col=1
    )
    
    # Humidity
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['humidity'], name='Humidity', line=dict(color='#4ECDC4')),
        row=1, col=2
    )
    
    # Light
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['light'], name='Light', line=dict(color='#FFE66D')),
        row=2, col=1
    )
    
    # Moisture
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['soil_moisture'], name='Moisture', line=dict(color='#8B4513')),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_health_score_gauge(score: int) -> go.Figure:
    """
    Create health score gauge chart
    
    Args:
        score: Health score (0-100)
        
    Returns:
        Plotly gauge figure
    """
    # Determine color based on score
    if score >= 85:
        color = "#2E8B57"  # Green
    elif score >= 70:
        color = "#FFE66D"  # Yellow
    else:
        color = "#FF6B6B"  # Red
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Plant Health Score"},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

def create_plant_status_chart(plant_data: Dict) -> go.Figure:
    """
    Create plant status radar chart
    
    Args:
        plant_data: Dictionary with plant sensor data
        
    Returns:
        Plotly radar chart
    """
    categories = ['Temperature', 'Humidity', 'Light', 'Moisture', 'pH', 'Nutrients']
    
    # Normalize values to 0-100 scale
    values = [
        min(100, max(0, (plant_data.get('temperature', 22) - 15) / 15 * 100)),
        min(100, max(0, plant_data.get('humidity', 60))),
        min(100, max(0, plant_data.get('light', 500) / 10)),
        min(100, max(0, plant_data.get('soil_moisture', 45))),
        min(100, max(0, (plant_data.get('ph', 6.5) - 5) / 3 * 100)),
        min(100, max(0, plant_data.get('nutrients', 75)))
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Status',
        line_color='#2E8B57'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Plant Status Overview",
        height=400
    )
    
    return fig
