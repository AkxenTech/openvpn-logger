#!/usr/bin/env python3
"""
Demo script for OpenVPN Logger
Generates sample OpenVPN log data for testing
"""

import os
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_sample_logs(log_path: str, num_events: int = 50):
    """Generate sample OpenVPN log entries"""
    
    # Ensure log directory exists
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample client IPs
    client_ips = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102",
        "10.0.0.50", "10.0.0.51", "10.0.0.52",
        "172.16.0.10", "172.16.0.11", "172.16.0.12"
    ]
    
    # Sample virtual IPs
    virtual_ips = [
        "10.8.0.2", "10.8.0.3", "10.8.0.4", "10.8.0.5",
        "10.8.0.6", "10.8.0.7", "10.8.0.8", "10.8.0.9"
    ]
    
    # Sample usernames
    usernames = [
        "john.doe", "jane.smith", "admin", "user1", "user2",
        "test.user", "demo.user", "vpn.user", "remote.user"
    ]
    
    events = []
    base_time = datetime.now() - timedelta(hours=2)
    
    for i in range(num_events):
        # Random timestamp within last 2 hours
        timestamp = base_time + timedelta(
            seconds=random.randint(0, 7200),
            milliseconds=random.randint(0, 999)
        )
        
        client_ip = random.choice(client_ips)
        client_port = random.randint(10000, 65000)
        username = random.choice(usernames)
        virtual_ip = random.choice(virtual_ips)
        
        # Generate different types of events
        event_type = random.choices(
            ['connect', 'authenticated', 'disconnect', 'auth_failed'],
            weights=[0.3, 0.4, 0.2, 0.1]
        )[0]
        
        if event_type == 'connect':
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Peer Connection Initiated with [AF_INET]{client_ip}:{client_port}\n"
        elif event_type == 'authenticated':
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {client_ip}:{client_port} MULTI: Learn: {virtual_ip}\n"
        elif event_type == 'disconnect':
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {client_ip}:{client_port} MULTI: primary virtual IP {virtual_ip}\n"
        elif event_type == 'auth_failed':
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {client_ip}:{client_port} AUTH: Failed\n"
        
        events.append((timestamp, log_line))
    
    # Sort events by timestamp
    events.sort(key=lambda x: x[0])
    
    # Write to log file
    with open(log_path, 'w') as f:
        for timestamp, log_line in events:
            f.write(log_line)
    
    print(f"Generated {num_events} sample log events in {log_path}")
    return events

def create_demo_environment():
    """Create a demo environment for testing"""
    
    print("Setting up demo environment...")
    
    # Create demo .env file
    demo_env_content = """# Demo MongoDB Configuration (Local)
MONGODB_URI=mongodb://localhost:27017/openvpn_logs_demo
MONGODB_DATABASE=openvpn_logs_demo
MONGODB_COLLECTION=connection_logs

# Demo OpenVPN Configuration
OPENVPN_LOG_PATH=./demo_openvpn.log
OPENVPN_STATUS_PATH=./demo_status.log

# Logging Configuration
LOG_LEVEL=INFO
LOG_INTERVAL=10  # seconds (faster for demo)

# Server Configuration
SERVER_NAME=demo-openvpn-server
SERVER_LOCATION=demo-location
"""
    
    with open('.env.demo', 'w') as f:
        f.write(demo_env_content)
    
    print("Created .env.demo file")
    
    # Generate sample logs
    generate_sample_logs('./demo_openvpn.log', 100)
    
    print("\nDemo environment created!")
    print("To run the demo:")
    print("1. Copy .env.demo to .env: cp .env.demo .env")
    print("2. Start MongoDB locally")
    print("3. Run: python openvpn_logger.py")
    print("4. In another terminal: python analyzer.py")

def run_demo():
    """Run a live demo with continuous log generation"""
    
    print("Starting live demo...")
    print("This will continuously generate log events and process them.")
    print("Press Ctrl+C to stop.\n")
    
    # Set up demo environment
    create_demo_environment()
    
    # Copy demo env to actual env
    import shutil
    shutil.copy('.env.demo', '.env')
    
    # Start the logger in a separate process
    import subprocess
    import signal
    import sys
    
    try:
        # Start the logger
        logger_process = subprocess.Popen([
            sys.executable, 'openvpn_logger.py'
        ])
        
        print("Logger started. Generating live events...")
        
        # Generate live events
        log_path = './demo_openvpn.log'
        event_count = 0
        
        while True:
            # Generate a few new events
            new_events = generate_sample_logs(log_path, 5)
            event_count += 5
            
            print(f"Generated {event_count} total events...")
            
            # Wait before generating more
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nStopping demo...")
        if 'logger_process' in locals():
            logger_process.terminate()
            logger_process.wait()
        print("Demo stopped.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenVPN Logger Demo')
    parser.add_argument('--setup', action='store_true', help='Set up demo environment')
    parser.add_argument('--live', action='store_true', help='Run live demo')
    parser.add_argument('--generate', type=int, default=50, help='Generate N sample events')
    
    args = parser.parse_args()
    
    if args.setup:
        create_demo_environment()
    elif args.live:
        run_demo()
    else:
        # Default: generate sample logs
        generate_sample_logs('./demo_openvpn.log', args.generate)
