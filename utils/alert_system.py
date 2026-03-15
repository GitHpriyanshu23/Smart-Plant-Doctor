#!/usr/bin/env python3
"""
Alert System for Smart Plant Doctor
Handles sensor data monitoring and alert generation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from alert_config import PLANT_THRESHOLDS, ALERT_LEVELS, ALERT_MESSAGES, ALERT_SETTINGS

# Import WhatsApp notifications
try:
    from utils.whatsapp_notifications import whatsapp_manager
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False
    whatsapp_manager = None

@dataclass
class Alert:
    """Represents a single alert"""
    id: str
    plant_name: str
    sensor_type: str
    current_value: float
    threshold_value: float
    severity: str
    message: str
    timestamp: datetime
    is_active: bool = True
    is_acknowledged: bool = False

class AlertSystem:
    """Main alert system for monitoring plant sensor data"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.last_check_time = datetime.now()
        self.rate_limiter = {}  # Track alerts per hour
        self.whatsapp_numbers = {}  # Store user WhatsApp numbers
        self.whatsapp_enabled = WHATSAPP_AVAILABLE and whatsapp_manager and whatsapp_manager.is_enabled()
        
    def check_sensor_data(self, plant_name: str, sensor_data: Dict[str, float]) -> List[Alert]:
        """
        Check sensor data against thresholds and generate alerts
        
        Args:
            plant_name: Name of the plant
            sensor_data: Dictionary with sensor readings
            
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        if plant_name not in PLANT_THRESHOLDS:
            return new_alerts
            
        thresholds = PLANT_THRESHOLDS[plant_name]
        
        for sensor_type, value in sensor_data.items():
            if sensor_type not in thresholds:
                continue
                
            sensor_thresholds = thresholds[sensor_type]
            min_val = sensor_thresholds["min"]
            max_val = sensor_thresholds["max"]
            ideal_val = sensor_thresholds["ideal"]
            
            # Check for low values
            if value < min_val:
                severity = self._calculate_severity(value, min_val, ideal_val, "low")
                alert = self._create_alert(
                    plant_name, sensor_type, value, min_val, 
                    f"{sensor_type}_low", severity
                )
                if alert and self._should_create_alert(alert):
                    new_alerts.append(alert)
                    
            # Check for high values
            elif value > max_val:
                severity = self._calculate_severity(value, max_val, ideal_val, "high")
                alert = self._create_alert(
                    plant_name, sensor_type, value, max_val,
                    f"{sensor_type}_high", severity
                )
                if alert and self._should_create_alert(alert):
                    new_alerts.append(alert)
        
        # Add new alerts to the system
        for alert in new_alerts:
            self.alerts.append(alert)
            self.alert_history.append(alert)
            
            # Send WhatsApp notification if enabled
            if self.whatsapp_enabled:
                self._send_whatsapp_alert(alert)
            
        return new_alerts
    
    def _calculate_severity(self, value: float, threshold: float, ideal: float, direction: str) -> str:
        """Calculate alert severity based on how far the value is from ideal"""
        if direction == "low":
            deviation = (ideal - value) / ideal
        else:
            deviation = (value - ideal) / ideal
            
        if deviation > 0.5:  # 50% deviation
            return "CRITICAL"
        elif deviation > 0.3:  # 30% deviation
            return "HIGH"
        elif deviation > 0.15:  # 15% deviation
            return "MEDIUM"
        else:
            return "LOW"
    
    def _create_alert(self, plant_name: str, sensor_type: str, value: float, 
                     threshold: float, alert_key: str, severity: str) -> Optional[Alert]:
        """Create a new alert"""
        alert_id = f"{plant_name}_{sensor_type}_{int(time.time())}"
        
        message_template = ALERT_MESSAGES.get(alert_key, "Alert for {plant_name}")
        message = message_template.format(
            plant_name=plant_name,
            value=round(value, 1),
            threshold=round(threshold, 1)
        )
        
        return Alert(
            id=alert_id,
            plant_name=plant_name,
            sensor_type=sensor_type,
            current_value=value,
            threshold_value=threshold,
            severity=severity,
            message=message,
            timestamp=datetime.now()
        )
    
    def _should_create_alert(self, alert: Alert) -> bool:
        """Check if alert should be created based on rate limiting and cooldown"""
        # Rate limiting check
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        rate_key = f"{alert.plant_name}_{alert.sensor_type}_{current_hour}"
        
        if rate_key not in self.rate_limiter:
            self.rate_limiter[rate_key] = 0
            
        if self.rate_limiter[rate_key] >= ALERT_SETTINGS["max_alerts_per_hour"]:
            return False
            
        # Cooldown check
        cooldown_time = datetime.now() - timedelta(minutes=ALERT_SETTINGS["alert_cooldown_minutes"])
        recent_alerts = [
            a for a in self.alert_history 
            if (a.plant_name == alert.plant_name and 
                a.sensor_type == alert.sensor_type and 
                a.timestamp > cooldown_time)
        ]
        
        if recent_alerts:
            return False
            
        # Update rate limiter
        self.rate_limiter[rate_key] += 1
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all currently active alerts"""
        return [alert for alert in self.alerts if alert.is_active]
    
    def get_alerts_by_plant(self, plant_name: str) -> List[Alert]:
        """Get active alerts for a specific plant"""
        return [
            alert for alert in self.alerts 
            if alert.plant_name == plant_name and alert.is_active
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.is_acknowledged = True
                return True
        return False
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert (mark as inactive)"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.is_active = False
                return True
        return False
    
    def dismiss_all_alerts(self) -> int:
        """Dismiss all active alerts"""
        count = 0
        for alert in self.alerts:
            if alert.is_active:
                alert.is_active = False
                count += 1
        return count
    
    def get_alert_summary(self) -> Dict:
        """Get summary of current alert status"""
        active_alerts = self.get_active_alerts()
        
        summary = {
            "total_active": len(active_alerts),
            "by_severity": {},
            "by_plant": {},
            "by_sensor": {}
        }
        
        # Count by severity
        for severity in ALERT_LEVELS.keys():
            summary["by_severity"][severity] = len([
                a for a in active_alerts if a.severity == severity
            ])
        
        # Count by plant
        plants = set(alert.plant_name for alert in active_alerts)
        for plant in plants:
            summary["by_plant"][plant] = len([
                a for a in active_alerts if a.plant_name == plant
            ])
        
        # Count by sensor type
        sensors = set(alert.sensor_type for alert in active_alerts)
        for sensor in sensors:
            summary["by_sensor"][sensor] = len([
                a for a in active_alerts if a.sensor_type == sensor
            ])
        
        return summary
    
    def cleanup_old_alerts(self, hours: int = 24):
        """Remove alerts older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Remove from active alerts
        self.alerts = [
            alert for alert in self.alerts 
            if alert.timestamp > cutoff_time
        ]
        
        # Keep only recent history
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert.timestamp > cutoff_time
        ]
    
    def add_whatsapp_number(self, plant_name: str, phone_number: str):
        """Add WhatsApp number for a specific plant"""
        # Format phone number for WhatsApp (add whatsapp: prefix if not present)
        if not phone_number.startswith('whatsapp:'):
            phone_number = f"whatsapp:{phone_number}"
        self.whatsapp_numbers[plant_name] = phone_number
    
    def remove_whatsapp_number(self, plant_name: str):
        """Remove WhatsApp number for a specific plant"""
        if plant_name in self.whatsapp_numbers:
            del self.whatsapp_numbers[plant_name]
    
    def get_whatsapp_numbers(self) -> Dict[str, str]:
        """Get all registered WhatsApp numbers"""
        return self.whatsapp_numbers.copy()
    
    def _send_whatsapp_alert(self, alert: Alert):
        """Send WhatsApp notification for an alert"""
        if not self.whatsapp_enabled or not whatsapp_manager:
            return
            
        # Get WhatsApp number for this plant
        whatsapp_number = self.whatsapp_numbers.get(alert.plant_name)
        if not whatsapp_number:
            return
            
        try:
            success = whatsapp_manager.send_plant_alert(
                to_number=whatsapp_number,
                alert_message=alert.message,
                plant_name=alert.plant_name,
                severity=alert.severity
            )
            
            if success:
                print(f"✅ WhatsApp alert sent for {alert.plant_name}")
            else:
                print(f"❌ Failed to send WhatsApp alert for {alert.plant_name}")
                
        except Exception as e:
            print(f"❌ Error sending WhatsApp alert: {str(e)}")
    
    def send_whatsapp_digest(self, plant_summary: Dict[str, Dict]) -> bool:
        """Send WhatsApp digest for all plants"""
        if not self.whatsapp_enabled or not whatsapp_manager:
            return False
            
        # Send digest to all registered numbers
        success_count = 0
        for plant_name, whatsapp_number in self.whatsapp_numbers.items():
            try:
                success = whatsapp_manager.send_daily_digest(whatsapp_number, plant_summary)
                if success:
                    success_count += 1
            except Exception as e:
                print(f"❌ Error sending digest to {plant_name}: {str(e)}")
        
        return success_count > 0
    
    def test_whatsapp_connection(self) -> bool:
        """Test WhatsApp API connection"""
        if not self.whatsapp_enabled or not whatsapp_manager:
            return False
        return whatsapp_manager.test_connection()
    
    def enable_whatsapp(self, account_sid: str, auth_token: str, from_number: str):
        """Enable WhatsApp notifications with Twilio credentials"""
        if whatsapp_manager:
            whatsapp_manager.update_config(account_sid, auth_token, from_number, True)
            self.whatsapp_enabled = whatsapp_manager.is_enabled()
    
    def disable_whatsapp(self):
        """Disable WhatsApp notifications"""
        if whatsapp_manager:
            whatsapp_manager.update_config("", "", "", False)
            self.whatsapp_enabled = False

# Global alert system instance
alert_system = AlertSystem()
