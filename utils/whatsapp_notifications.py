#!/usr/bin/env python3
"""
WhatsApp Notifications for Smart Plant Doctor
Handles sending plant alerts via WhatsApp using Twilio API
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import time

@dataclass
class WhatsAppConfig:
    """WhatsApp configuration settings"""
    account_sid: str
    auth_token: str
    from_number: str  # Twilio WhatsApp number (e.g., whatsapp:+14155238886)
    enabled: bool = False

class WhatsAppNotifier:
    """Handles WhatsApp notifications for plant alerts"""
    
    def __init__(self, config: WhatsAppConfig):
        self.config = config
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}/Messages.json"
        self.session = requests.Session()
        self.session.auth = (config.account_sid, config.auth_token)
        
    def send_alert(self, to_number: str, alert_message: str, plant_name: str, severity: str) -> bool:
        """
        Send a single alert via WhatsApp
        
        Args:
            to_number: Recipient's WhatsApp number (e.g., whatsapp:+1234567890)
            alert_message: The alert message to send
            plant_name: Name of the plant
            severity: Alert severity level
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.config.enabled:
            print(f"WhatsApp notifications disabled. Would send: {alert_message}")
            return False
            
        try:
            # Format the message with emojis based on severity
            emoji_map = {
                "LOW": "⚠️",
                "MEDIUM": "🚨", 
                "HIGH": "🚨",
                "CRITICAL": "🚨"
            }
            
            emoji = emoji_map.get(severity, "🌱")
            
            # Create formatted message
            formatted_message = f"""
{emoji} *Smart Plant Doctor Alert*

🌱 *Plant:* {plant_name}
{emoji} *Severity:* {severity}
📅 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{alert_message}

---
Reply STOP to unsubscribe from alerts.
            """.strip()
            
            # Send message via Twilio API
            data = {
                'From': self.config.from_number,
                'To': to_number,
                'Body': formatted_message
            }
            
            response = self.session.post(self.base_url, data=data)
            
            if response.status_code == 201:
                print(f"✅ WhatsApp alert sent successfully to {to_number}")
                return True
            else:
                print(f"❌ Failed to send WhatsApp alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending WhatsApp alert: {str(e)}")
            return False
    
    def send_bulk_alerts(self, alerts: List[Dict]) -> Dict[str, bool]:
        """
        Send multiple alerts via WhatsApp
        
        Args:
            alerts: List of alert dictionaries with 'to_number', 'message', 'plant_name', 'severity'
            
        Returns:
            Dict mapping alert IDs to success status
        """
        results = {}
        
        for alert in alerts:
            success = self.send_alert(
                to_number=alert['to_number'],
                alert_message=alert['message'],
                plant_name=alert['plant_name'],
                severity=alert['severity']
            )
            results[alert.get('id', 'unknown')] = success
            
            # Add small delay between messages to avoid rate limiting
            time.sleep(1)
            
        return results
    
    def send_digest(self, to_number: str, plant_summary: Dict) -> bool:
        """
        Send a daily digest of plant status
        
        Args:
            to_number: Recipient's WhatsApp number
            plant_summary: Summary of all plants and their status
            
        Returns:
            bool: True if digest sent successfully
        """
        if not self.config.enabled:
            print(f"WhatsApp digest disabled. Would send: {plant_summary}")
            return False
            
        try:
            message = f"""
🌱 *Smart Plant Doctor - Daily Digest*
📅 {datetime.now().strftime('%Y-%m-%d')}

*Plant Status Summary:*
"""
            
            for plant, status in plant_summary.items():
                if status['alerts'] > 0:
                    message += f"🚨 {plant}: {status['alerts']} active alerts\n"
                else:
                    message += f"✅ {plant}: Healthy\n"
            
            message += "\nVisit your dashboard for detailed information."
            
            return self.send_alert(to_number, message, "All Plants", "INFO")
            
        except Exception as e:
            print(f"❌ Error sending digest: {str(e)}")
            return False

class WhatsAppManager:
    """Manages WhatsApp notifications and user preferences"""
    
    def __init__(self, config_file: str = "whatsapp_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.notifier = WhatsAppNotifier(self.config)
        
    def _load_config(self) -> WhatsAppConfig:
        """Load WhatsApp configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return WhatsAppConfig(**data)
            else:
                # Create default config
                default_config = WhatsAppConfig(
                    account_sid="",
                    auth_token="",
                    from_number="",
                    enabled=False
                )
                self._save_config(default_config)
                return default_config
        except Exception as e:
            print(f"❌ Error loading WhatsApp config: {str(e)}")
            return WhatsAppConfig("", "", "", False)
    
    def _save_config(self, config: WhatsAppConfig):
        """Save WhatsApp configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'account_sid': config.account_sid,
                    'auth_token': config.auth_token,
                    'from_number': config.from_number,
                    'enabled': config.enabled
                }, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving WhatsApp config: {str(e)}")
    
    def update_config(self, account_sid: str, auth_token: str, from_number: str, enabled: bool = True):
        """Update WhatsApp configuration"""
        self.config = WhatsAppConfig(account_sid, auth_token, from_number, enabled)
        self._save_config(self.config)
        self.notifier = WhatsAppNotifier(self.config)
    
    def test_connection(self) -> bool:
        """Test WhatsApp API connection"""
        if not self.config.enabled or not self.config.account_sid:
            return False
            
        try:
            # Test with a simple API call
            test_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.account_sid}.json"
            response = self.notifier.session.get(test_url)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ WhatsApp connection test failed: {str(e)}")
            return False
    
    def send_plant_alert(self, to_number: str, alert_message: str, plant_name: str, severity: str) -> bool:
        """Send a plant alert via WhatsApp"""
        return self.notifier.send_alert(to_number, alert_message, plant_name, severity)
    
    def send_bulk_alerts(self, alerts: List[Dict]) -> Dict[str, bool]:
        """Send multiple alerts via WhatsApp"""
        return self.notifier.send_bulk_alerts(alerts)
    
    def send_daily_digest(self, to_number: str, plant_summary: Dict) -> bool:
        """Send daily plant status digest"""
        return self.notifier.send_digest(to_number, plant_summary)
    
    def is_enabled(self) -> bool:
        """Check if WhatsApp notifications are enabled"""
        return self.config.enabled and bool(self.config.account_sid)

# Global WhatsApp manager instance
whatsapp_manager = WhatsAppManager()
