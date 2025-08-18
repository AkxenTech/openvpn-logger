#!/usr/bin/env python3
"""
Debug script to investigate duplicate disconnect notifications
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_positions_file():
    """Check the positions.json file for issues"""
    position_file = Path("/var/log/openvpn/positions.json")
    
    print("🔍 Checking positions.json file...")
    print(f"File exists: {position_file.exists()}")
    
    if position_file.exists():
        try:
            with open(position_file, 'r') as f:
                positions = json.load(f)
            
            print(f"Status position: {positions.get('status_position', 0)}")
            print(f"Log position: {positions.get('log_position', 0)}")
            print(f"Notified sessions count: {len(positions.get('notified_sessions', []))}")
            
            # Show some notified sessions
            notified = positions.get('notified_sessions', [])
            if notified:
                print("Recent notified sessions:")
                for session in notified[-10:]:  # Last 10
                    print(f"  - {session}")
            
        except Exception as e:
            print(f"Error reading positions file: {e}")
    else:
        print("❌ Positions file not found!")

def check_log_files():
    """Check log file sizes and timestamps"""
    print("\n📄 Checking log files...")
    
    status_path = Path(os.getenv('OPENVPN_STATUS_PATH', '/var/log/openvpn/status.log'))
    log_path = Path(os.getenv('OPENVPN_LOG_PATH', '/var/log/openvpn/server.log'))
    
    print(f"Status log: {status_path}")
    print(f"  Exists: {status_path.exists()}")
    if status_path.exists():
        stat = status_path.stat()
        print(f"  Size: {stat.st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(stat.st_mtime)}")
    
    print(f"Main log: {log_path}")
    print(f"  Exists: {log_path.exists()}")
    if log_path.exists():
        stat = log_path.stat()
        print(f"  Size: {stat.st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(stat.st_mtime)}")

def check_recent_logs():
    """Check recent log entries for disconnect patterns"""
    print("\n📝 Checking recent log entries...")
    
    log_path = Path(os.getenv('OPENVPN_LOG_PATH', '/var/log/openvpn/server.log'))
    
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            print(f"Total lines in log: {len(lines)}")
            
            # Look for disconnect patterns
            disconnect_lines = []
            for i, line in enumerate(lines[-50:], max(0, len(lines)-50)):  # Last 50 lines
                if 'SIGTERM[soft,remote-exit]' in line:
                    disconnect_lines.append((i, line.strip()))
            
            print(f"Disconnect lines found: {len(disconnect_lines)}")
            for line_num, line in disconnect_lines:
                print(f"  Line {line_num}: {line}")
                
        except Exception as e:
            print(f"Error reading log file: {e}")

def check_service_logs():
    """Check recent service logs"""
    print("\n🔧 Checking recent service logs...")
    
    try:
        import subprocess
        result = subprocess.run(['sudo', 'journalctl', '-u', 'openvpn-logger', '-n', '20', '--no-pager'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print("Recent service logs:")
            for line in lines[-10:]:  # Last 10 lines
                if 'disconnect' in line.lower() or 'duplicate' in line.lower():
                    print(f"  {line}")
        else:
            print("Could not read service logs")
            
    except Exception as e:
        print(f"Error checking service logs: {e}")

def check_mongodb_duplicates():
    """Check MongoDB for duplicate disconnect entries"""
    print("\n🗄️ Checking MongoDB for duplicates...")
    
    try:
        from pymongo import MongoClient
        
        uri = os.getenv('MONGODB_URI')
        database = os.getenv('MONGODB_DATABASE', 'openvpn_logs')
        collection = os.getenv('MONGODB_COLLECTION', 'connection_logs')
        
        if not uri:
            print("❌ MONGODB_URI not set")
            return
        
        client = MongoClient(uri)
        db = client[database]
        coll = db[collection]
        
        # Check recent disconnect events
        recent_disconnects = list(coll.find({
            'event_type': 'disconnect',
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=1)}
        }).sort('timestamp', -1))
        
        print(f"Recent disconnect events (last hour): {len(recent_disconnects)}")
        
        # Group by session to find duplicates
        session_counts = {}
        for event in recent_disconnects:
            session_id = f"{event.get('client_ip')}:{event.get('client_port')}"
            if session_id not in session_counts:
                session_counts[session_id] = []
            session_counts[session_id].append(event)
        
        # Show duplicates
        duplicates = {session: events for session, events in session_counts.items() if len(events) > 1}
        
        if duplicates:
            print(f"❌ Found {len(duplicates)} sessions with duplicate disconnects:")
            for session, events in duplicates.items():
                print(f"  Session {session}: {len(events)} disconnect events")
                for event in events:
                    print(f"    - {event.get('timestamp')} - {event.get('username', 'Unknown')}")
        else:
            print("✅ No duplicate disconnects found in MongoDB")
            
    except Exception as e:
        print(f"Error checking MongoDB: {e}")

def main():
    """Main debug function"""
    print("🔍 OpenVPN Logger Duplicate Disconnect Debug Tool")
    print("=" * 50)
    
    check_positions_file()
    check_log_files()
    check_recent_logs()
    check_service_logs()
    check_mongodb_duplicates()
    
    print("\n" + "=" * 50)
    print("💡 Debug complete. Check the output above for issues.")

if __name__ == "__main__":
    main()
