#!/usr/bin/env python3
"""
Notification system for OpenVPN Logger using Pushover API
"""

import os
import requests
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Pushover notification configuration"""
    api_token: str
    user_key: str
    device: Optional[str] = None
    priority: int = 0  # -2 to 2
    sound: Optional[str] = None
    url: Optional[str] = None
    url_title: Optional[str] = None


class PushoverNotifier:
    """Handles Pushover notifications"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.api_url = "https://api.pushover.net/1/messages.json"
    
    def send_notification(self, title: str, message: str, priority: int = None) -> bool:
        """Send a notification via Pushover"""
        try:
            payload = {
                'token': self.config.api_token,
                'user': self.config.user_key,
                'title': title,
                'message': message,
                'priority': priority if priority is not None else self.config.priority,
                'sound': self.config.sound,
                'url': self.config.url,
                'url_title': self.config.url_title
            }
            
            # Add device if specified
            if self.config.device:
                payload['device'] = self.config.device
            
            response = requests.post(self.api_url, data=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('status') == 1:
                logger.info(f"Pushover notification sent: {title}")
                return True
            else:
                logger.error(f"Pushover API error: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {e}")
            return False
    
    def notify_connection_event(self, event_type: str, client_ip: str, username: str = None, 
                              virtual_ip: str = None, server_name: str = None, client_port: int = None) -> bool:
        """Send notification for connection events"""
        
        # Determine notification settings based on event type
        if event_type == 'connect':
            title = "🔗 OpenVPN User Connected"
            priority = 0
            sound = "cosmic"
        elif event_type == 'disconnect':
            title = "🔌 OpenVPN User Disconnected"
            priority = 0
            sound = "pushover"
        elif event_type == 'auth_failed':
            title = "⚠️ OpenVPN Auth Failed"
            priority = 1
            sound = "siren"
        else:
            title = f"ℹ️ OpenVPN {event_type.title()}"
            priority = 0
            sound = "pushover"
        
        # Build message
        message_parts = []
        if username and username != 'UNDEF':
            message_parts.append(f"User: {username}")
        
        # Include port number in IP display
        if client_port:
            message_parts.append(f"IP: {client_ip}:{client_port}")
        else:
            message_parts.append(f"IP: {client_ip}")
            
        if virtual_ip:
            message_parts.append(f"Virtual IP: {virtual_ip}")
        if server_name:
            message_parts.append(f"Server: {server_name}")
        message_parts.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        message = "\n".join(message_parts)
        
        return self.send_notification(title, message, priority)
    
    def notify_system_alert(self, alert_type: str, details: str, server_name: str = None) -> bool:
        """Send notification for system alerts"""
        title = f"🚨 System Alert: {alert_type}"
        message = f"{details}\nServer: {server_name or 'Unknown'}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(title, message, priority=1)
    
    def notify_summary(self, stats: Dict, server_name: str = None) -> bool:
        """Send daily summary notification"""
        title = "📊 OpenVPN Daily Summary"
        
        message_parts = []
        if 'connect' in stats:
            message_parts.append(f"Connections: {stats['connect']['count']}")
        if 'disconnect' in stats:
            message_parts.append(f"Disconnections: {stats['disconnect']['count']}")
        if 'auth_failed' in stats:
            message_parts.append(f"Auth Failures: {stats['auth_failed']['count']}")
        
        if server_name:
            message_parts.append(f"Server: {server_name}")
        message_parts.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        
        message = "\n".join(message_parts)
        
        return self.send_notification(title, message, priority=-1)  # Low priority for summaries


class NotificationManager:
    """Manages all notification systems"""
    
    def __init__(self):
        self.pushover = None
        self.enabled = False
        self.setup_notifications()
    
    def setup_notifications(self):
        """Setup notification systems based on environment variables"""
        # Check if Pushover is configured
        api_token = os.getenv('PUSHOVER_API_TOKEN')
        user_key = os.getenv('PUSHOVER_USER_KEY')
        
        if api_token and user_key:
            config = NotificationConfig(
                api_token=api_token,
                user_key=user_key,
                device=os.getenv('PUSHOVER_DEVICE'),
                priority=int(os.getenv('PUSHOVER_PRIORITY', '0')),
                sound=os.getenv('PUSHOVER_SOUND'),
                url=os.getenv('PUSHOVER_URL'),
                url_title=os.getenv('PUSHOVER_URL_TITLE')
            )
            
            self.pushover = PushoverNotifier(config)
            self.enabled = True
            logger.info("Pushover notifications enabled")
        else:
            logger.info("Pushover notifications disabled - missing API_TOKEN or USER_KEY")
    
    def notify_connection_event(self, event_type: str, client_ip: str, username: str = None,
                              virtual_ip: str = None, server_name: str = None, client_port: int = None) -> bool:
        """Send notification for connection events"""
        if not self.enabled or not self.pushover:
            return False
        
        return self.pushover.notify_connection_event(event_type, client_ip, username, virtual_ip, server_name, client_port)
    
    def notify_system_alert(self, alert_type: str, details: str, server_name: str = None) -> bool:
        """Send notification for system alerts"""
        if not self.enabled or not self.pushover:
            return False
        
        return self.pushover.notify_system_alert(alert_type, details, server_name)
    
    def notify_summary(self, stats: Dict, server_name: str = None) -> bool:
        """Send daily summary notification"""
        if not self.enabled or not self.pushover:
            return False
        
        return self.pushover.notify_summary(stats, server_name)

