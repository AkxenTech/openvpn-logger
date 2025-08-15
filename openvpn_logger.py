#!/usr/bin/env python3
"""
OpenVPN Logger - Monitors and logs OpenVPN connection data to MongoDB
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

import pymongo
from dotenv import load_dotenv
import psutil
import netifaces
from notifications import NotificationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ConnectionEvent:
    """Represents an OpenVPN connection event"""
    timestamp: datetime
    event_type: str  # 'connect', 'disconnect', 'auth_failed', etc.
    client_ip: str
    client_port: int
    username: Optional[str] = None
    virtual_ip: Optional[str] = None
    bytes_received: Optional[int] = None
    bytes_sent: Optional[int] = None
    session_duration: Optional[int] = None
    server_name: str = None
    server_location: str = None


class OpenVPNLogParser:
    """Parses OpenVPN log files to extract connection events"""
    
    def __init__(self, status_path: str, log_path: str = None):
        self.status_path = Path(status_path)
        self.log_path = Path(log_path) if log_path else None
        self.last_position = 0
        self.last_clients = set()  # Track previous clients for change detection
        self.active_sessions = {}  # Track active sessions to prevent duplicate notifications
        self.log_last_position = 0  # Track position in main log file
        
    def get_new_lines(self) -> List[str]:
        """Read new lines from the status log file since last check"""
        if not self.status_path.exists():
            logger.warning(f"OpenVPN status log file not found: {self.status_path}")
            return []
            
        try:
            with open(self.status_path, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                return new_lines
        except Exception as e:
            logger.error(f"Error reading status log file: {e}")
            return []
    
    def get_new_log_lines(self) -> List[str]:
        """Read new lines from the main OpenVPN log file since last check"""
        if not self.log_path or not self.log_path.exists():
            return []
            
        try:
            with open(self.log_path, 'r') as f:
                f.seek(self.log_last_position)
                new_lines = f.readlines()
                self.log_last_position = f.tell()
                return new_lines
        except Exception as e:
            logger.error(f"Error reading main log file: {e}")
            return []
    
    def extract_username_from_log(self, line: str) -> tuple:
        """Extract username and session info from log line"""
        # Pattern: IP:PORT [username] Peer Connection Initiated
        import re
        pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)\s+\[([^\]]+)\]\s+Peer Connection Initiated'
        match = re.search(pattern, line)
        
        if match:
            client_ip = match.group(1)
            client_port = int(match.group(2))
            username = match.group(3)
            session_id = f"{client_ip}:{client_port}"
            return username, session_id, client_ip, client_port
        
        return None, None, None, None
    
    def detect_logout_from_log(self, line: str) -> tuple:
        """Detect logout events from SIGTERM messages"""
        # Pattern: username/IP:PORT SIGTERM[soft,remote-exit] received
        import re
        pattern = r'([^/]+)/(\d+\.\d+\.\d+\.\d+):(\d+)\s+SIGTERM\[soft,remote-exit\]'
        match = re.search(pattern, line)
        
        if match:
            username = match.group(1)
            client_ip = match.group(2)
            client_port = int(match.group(3))
            session_id = f"{client_ip}:{client_port}"
            return username, session_id, client_ip, client_port
        
        return None, None, None, None
    
    def parse_status_log(self, content: str) -> List[ConnectionEvent]:
        """Parse the entire status log content and extract connection events"""
        events = []
        lines = content.split('\n')
        
        current_clients = set()
        
        for line in lines:
            if line.startswith('CLIENT_LIST,'):
                # Parse client information
                parts = line.split(',')
                if len(parts) >= 8:
                    common_name = parts[1]
                    real_address = parts[2]
                    virtual_address = parts[3]
                    virtual_ipv6 = parts[4]
                    bytes_received = int(parts[5]) if parts[5].isdigit() else 0
                    bytes_sent = int(parts[6]) if parts[6].isdigit() else 0
                    connected_since = parts[7]
                    username = parts[9] if len(parts) > 9 else None
                    
                    # Parse real address
                    if ':' in real_address:
                        client_ip, client_port = real_address.rsplit(':', 1)
                        client_port = int(client_port)
                    else:
                        client_ip = real_address
                        client_port = 0
                    
                    # Create unique client identifier
                    client_id = f"{client_ip}:{client_port}"
                    current_clients.add(client_id)
                    
                    # Check if this is a new client (connect event)
                    if client_id not in self.last_clients:
                        events.append(ConnectionEvent(
                            timestamp=datetime.now(),
                            event_type='connect',
                            client_ip=client_ip,
                            client_port=client_port,
                            username=username,
                            virtual_ip=virtual_address,
                            bytes_received=bytes_received,
                            bytes_sent=bytes_sent,
                            server_name=os.getenv('SERVER_NAME'),
                            server_location=os.getenv('SERVER_LOCATION')
                        ))
                    
                    # Also create an authenticated event for current connections
                    events.append(ConnectionEvent(
                        timestamp=datetime.now(),
                        event_type='authenticated',
                        client_ip=client_ip,
                        client_port=client_port,
                        username=username,
                        virtual_ip=virtual_address,
                        bytes_received=bytes_received,
                        bytes_sent=bytes_sent,
                        server_name=os.getenv('SERVER_NAME'),
                        server_location=os.getenv('SERVER_LOCATION')
                    ))
        
        # Check for disconnected clients
        for client_id in self.last_clients - current_clients:
            if ':' in client_id:
                client_ip, client_port = client_id.rsplit(':', 1)
                client_port = int(client_port)
            else:
                client_ip = client_id
                client_port = 0
                
            events.append(ConnectionEvent(
                timestamp=datetime.now(),
                event_type='disconnect',
                client_ip=client_ip,
                client_port=client_port,
                server_name=os.getenv('SERVER_NAME'),
                server_location=os.getenv('SERVER_LOCATION')
            ))
        
        # Update last clients
        self.last_clients = current_clients
        
        return events
    
    def process_logs(self) -> List[ConnectionEvent]:
        """Process both log files and return new events"""
        events = []
        
        try:
            # Process main log file for usernames and logout events
            if self.log_path and self.log_path.exists():
                log_lines = self.get_new_log_lines()
                for line in log_lines:
                    # Check for login events with username
                    username, session_id, client_ip, client_port = self.extract_username_from_log(line)
                    if username and session_id:
                        # Store username for this session
                        self.active_sessions[session_id] = username
                        logger.debug(f"Found login for user {username} with session {session_id}")
                    
                    # Check for logout events
                    username, session_id, client_ip, client_port = self.detect_logout_from_log(line)
                    if username and session_id:
                        # Create logout event
                        events.append(ConnectionEvent(
                            timestamp=datetime.now(),
                            event_type='disconnect',
                            client_ip=client_ip,
                            client_port=client_port,
                            username=username,
                            server_name=os.getenv('SERVER_NAME'),
                            server_location=os.getenv('SERVER_LOCATION')
                        ))
                        # Remove from active sessions
                        if session_id in self.active_sessions:
                            del self.active_sessions[session_id]
                        logger.debug(f"Found logout for user {username} with session {session_id}")
            
            # Process status log for connection events
            if self.status_path.exists():
                with open(self.status_path, 'r') as f:
                    content = f.read()
                
                # Parse status log events
                status_events = self.parse_status_log(content)
                
                # Filter and enhance events with usernames
                for event in status_events:
                    session_id = f"{event.client_ip}:{event.client_port}"
                    
                    # Add username if available from active sessions
                    if session_id in self.active_sessions:
                        event.username = self.active_sessions[session_id]
                    
                    # Only add connect events if we haven't seen this session before
                    if event.event_type == 'connect':
                        if session_id not in self.active_sessions:
                            events.append(event)
                            logger.debug(f"New connection event for session {session_id}")
                        else:
                            logger.debug(f"Skipping duplicate connect event for session {session_id}")
                    else:
                        events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error processing logs: {e}")
            return []


class MongoDBLogger:
    """Handles MongoDB operations for storing connection logs"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            uri = os.getenv('MONGODB_URI')
            database = os.getenv('MONGODB_DATABASE', 'openvpn_logs')
            collection = os.getenv('MONGODB_COLLECTION', 'connection_logs')
            
            if not uri:
                logger.error("MONGODB_URI not set in environment variables")
                return
            
            self.client = pymongo.MongoClient(uri)
            self.db = self.client[database]
            self.collection = self.db[collection]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
    
    def log_connection_event(self, event: ConnectionEvent):
        """Log a connection event to MongoDB"""
        if self.collection is None:
            logger.error("MongoDB not connected")
            return
            
        try:
            # Convert dataclass to dict
            event_dict = {
                'timestamp': event.timestamp,
                'event_type': event.event_type,
                'client_ip': event.client_ip,
                'client_port': event.client_port,
                'username': event.username,
                'virtual_ip': event.virtual_ip,
                'bytes_received': event.bytes_received,
                'bytes_sent': event.bytes_sent,
                'session_duration': event.session_duration,
                'server_name': event.server_name,
                'server_location': event.server_location,
                'created_at': datetime.utcnow()
            }
            
            # Remove None values
            event_dict = {k: v for k, v in event_dict.items() if v is not None}
            
            result = self.collection.insert_one(event_dict)
            logger.info(f"Logged {event.event_type} event for {event.client_ip}:{event.client_port}")
            
        except Exception as e:
            logger.error(f"Failed to log connection event: {e}")
    
    def get_connection_stats(self, hours: int = 24) -> Dict:
        """Get connection statistics for the last N hours"""
        if self.collection is None:
            return {}
            
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {'$match': {'timestamp': {'$gte': cutoff_time}}},
                {'$group': {
                    '_id': '$event_type',
                    'count': {'$sum': 1},
                    'unique_clients': {'$addToSet': '$client_ip'}
                }},
                {'$project': {
                    'event_type': '$_id',
                    'count': 1,
                    'unique_clients': {'$size': '$unique_clients'}
                }}
            ]
            
            stats = list(self.collection.aggregate(pipeline))
            return {stat['event_type']: stat for stat in stats}
            
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {}


class SystemMonitor:
    """Monitors system resources and network interfaces"""
    
    @staticmethod
    def get_system_stats() -> Dict:
        """Get current system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_percent': disk.percent,
                'disk_free': disk.free
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    @staticmethod
    def get_network_interfaces() -> Dict:
        """Get network interface information"""
        try:
            interfaces = {}
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    interfaces[interface] = {
                        'ip': addrs[netifaces.AF_INET][0]['addr'],
                        'netmask': addrs[netifaces.AF_INET][0]['netmask']
                    }
            return interfaces
        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")
            return {}


class OpenVPNLogger:
    """Main OpenVPN logger application"""
    
    def __init__(self):
        status_path = os.getenv('OPENVPN_STATUS_PATH')
        log_path = os.getenv('OPENVPN_LOG_PATH')
        self.parser = OpenVPNLogParser(status_path, log_path)
        self.mongo_logger = MongoDBLogger()
        self.system_monitor = SystemMonitor()
        self.notification_manager = NotificationManager()
        self.running = False
    
    def process_logs(self):
        """Process new log entries"""
        try:
            events = self.parser.process_logs()
            
            for event in events:
                self.mongo_logger.log_connection_event(event)
                
                # Send notification for connection events
                self.notification_manager.notify_connection_event(
                    event_type=event.event_type,
                    client_ip=event.client_ip,
                    username=event.username,
                    virtual_ip=event.virtual_ip,
                    server_name=event.server_name
                )
                    
        except Exception as e:
            logger.error(f"Error processing logs: {e}")
    
    def log_system_stats(self):
        """Log system statistics"""
        try:
            stats = self.system_monitor.get_system_stats()
            interfaces = self.system_monitor.get_network_interfaces()
            
            if self.mongo_logger.collection is not None:
                system_data = {
                    'timestamp': datetime.utcnow(),
                    'type': 'system_stats',
                    'stats': stats,
                    'interfaces': interfaces,
                    'server_name': os.getenv('SERVER_NAME'),
                    'server_location': os.getenv('SERVER_LOCATION')
                }
                
                self.mongo_logger.collection.insert_one(system_data)
                logger.debug("Logged system statistics")
                
        except Exception as e:
            logger.error(f"Error logging system stats: {e}")
    
    def start(self):
        """Start the OpenVPN logger"""
        logger.info("Starting OpenVPN Logger...")
        self.running = True
        
        # Schedule tasks
        log_interval = int(os.getenv('LOG_INTERVAL', 60))
        schedule.every(log_interval).seconds.do(self.process_logs)
        schedule.every(300).seconds.do(self.log_system_stats)  # Every 5 minutes
        
        # Initial processing
        self.process_logs()
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Stopping OpenVPN Logger...")
            self.running = False
    
    def stop(self):
        """Stop the OpenVPN logger"""
        self.running = False


def main():
    """Main entry point"""
    logger = OpenVPNLogger()
    logger.start()


if __name__ == "__main__":
    main()
