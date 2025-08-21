#!/usr/bin/env python3

"""
Test script to verify OpenVPN Logger notification functionality
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notifications import NotificationManager
from openvpn_logger import ConnectionEvent, Config

def test_notification_manager():
    """Test the notification manager setup"""
    print("Testing Notification Manager Setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if Pushover is configured
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    user_key = os.getenv('PUSHOVER_USER_KEY')
    
    if not api_token or not user_key:
        print("❌ Pushover not configured. Set PUSHOVER_API_TOKEN and PUSHOVER_USER_KEY in .env")
        return False
    
    print(f"✓ Pushover API Token: {api_token[:10]}...")
    print(f"✓ Pushover User Key: {user_key[:10]}...")
    
    # Test notification manager initialization
    try:
        notification_manager = NotificationManager()
        if notification_manager.enabled:
            print("✓ Notification manager initialized successfully")
            return True
        else:
            print("❌ Notification manager not enabled")
            return False
    except Exception as e:
        print(f"❌ Failed to initialize notification manager: {e}")
        return False

def test_connection_events():
    """Test sending notifications for different event types"""
    print("\nTesting Connection Event Notifications...")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize notification manager
    notification_manager = NotificationManager()
    
    if not notification_manager.enabled:
        print("❌ Notification manager not enabled")
        return False
    
    # Test events
    test_events = [
        {
            'event_type': 'connect',
            'client_ip': '192.168.1.100',
            'client_port': 12345,
            'username': 'testuser',
            'virtual_ip': '10.8.0.2'
        },
        {
            'event_type': 'authenticated',
            'client_ip': '192.168.1.101',
            'client_port': 12346,
            'username': 'testuser2',
            'virtual_ip': '10.8.0.3'
        },
        {
            'event_type': 'disconnect',
            'client_ip': '192.168.1.102',
            'client_port': 12347,
            'username': 'testuser3',
            'virtual_ip': '10.8.0.4'
        }
    ]
    
    success_count = 0
    for event_data in test_events:
        print(f"\nTesting {event_data['event_type']} event...")
        
        try:
            result = notification_manager.notify_connection_event(
                event_type=event_data['event_type'],
                client_ip=event_data['client_ip'],
                username=event_data['username'],
                virtual_ip=event_data['virtual_ip'],
                server_name=Config.get_server_config()['name'],
                client_port=event_data['client_port']
            )
            
            if result:
                print(f"✓ {event_data['event_type']} notification sent successfully")
                success_count += 1
            else:
                print(f"❌ {event_data['event_type']} notification failed")
                
        except Exception as e:
            print(f"❌ Error sending {event_data['event_type']} notification: {e}")
    
    print(f"\nNotification Test Results: {success_count}/{len(test_events)} successful")
    return success_count == len(test_events)

def test_system_alert():
    """Test system alert notification"""
    print("\nTesting System Alert Notification...")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize notification manager
    notification_manager = NotificationManager()
    
    if not notification_manager.enabled:
        print("❌ Notification manager not enabled")
        return False
    
    try:
        result = notification_manager.notify_system_alert(
            alert_type="Test Alert",
            details="This is a test system alert from the notification test script",
            server_name=Config.get_server_config()['name']
        )
        
        if result:
            print("✓ System alert notification sent successfully")
            return True
        else:
            print("❌ System alert notification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error sending system alert notification: {e}")
        return False

def debug_status_log():
    """Debug the status log format"""
    print("\nDebugging Status Log Format...")
    
    # Load environment variables
    load_dotenv()
    
    from openvpn_logger import OpenVPNLogParser
    
    status_path = os.getenv('OPENVPN_STATUS_PATH', '/var/log/openvpn/status.log')
    log_path = os.getenv('OPENVPN_LOG_PATH', '/var/log/openvpn/server.log')
    
    try:
        parser = OpenVPNLogParser(status_path, log_path)
        parser.debug_status_log_format()
        print("✓ Status log format debug completed")
        return True
    except Exception as e:
        print(f"❌ Error debugging status log: {e}")
        return False

def main():
    """Main test function"""
    print("OpenVPN Logger Notification Test")
    print("=" * 40)
    
    # Check if user wants to debug status log
    if len(sys.argv) > 1 and sys.argv[1] == '--debug-status':
        return debug_status_log()
    
    # Test notification manager setup
    if not test_notification_manager():
        print("\n❌ Notification manager setup failed. Check your .env configuration.")
        return False
    
    # Test connection events
    if not test_connection_events():
        print("\n❌ Connection event notifications failed.")
        return False
    
    # Test system alert
    if not test_system_alert():
        print("\n❌ System alert notification failed.")
        return False
    
    print("\n🎉 All notification tests passed!")
    print("Check your device for the test notifications.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
