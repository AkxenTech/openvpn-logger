#!/usr/bin/env python3
"""
Configuration utility for OpenVPN Logger
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for OpenVPN Logger"""
    
    @staticmethod
    def get_mongodb_config() -> Dict[str, str]:
        """Get MongoDB configuration"""
        return {
            'uri': os.getenv('MONGODB_URI'),
            'database': os.getenv('MONGODB_DATABASE', 'openvpn_logs'),
            'collection': os.getenv('MONGODB_COLLECTION', 'connection_logs')
        }
    
    @staticmethod
    def get_openvpn_config() -> Dict[str, str]:
        """Get OpenVPN configuration"""
        return {
            'log_path': os.getenv('OPENVPN_LOG_PATH', '/var/log/openvpn/openvpn.log'),
            'status_path': os.getenv('OPENVPN_STATUS_PATH', '/var/log/openvpn/status.log')
        }
    
    @staticmethod
    def get_logging_config() -> Dict[str, any]:
        """Get logging configuration"""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'interval': int(os.getenv('LOG_INTERVAL', 60))
        }
    
    @staticmethod
    def get_server_config() -> Dict[str, str]:
        """Get server configuration"""
        return {
            'name': os.getenv('SERVER_NAME', 'openvpn-server-01'),
            'location': os.getenv('SERVER_LOCATION', 'us-east-1')
        }
    
    @staticmethod
    def validate_config() -> bool:
        """Validate that all required configuration is present"""
        required_vars = ['MONGODB_URI']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file or environment variables.")
            return False
        
        return True
    
    @staticmethod
    def print_config():
        """Print current configuration"""
        print("=== OpenVPN Logger Configuration ===")
        print(f"MongoDB URI: {os.getenv('MONGODB_URI', 'NOT SET')}")
        print(f"MongoDB Database: {os.getenv('MONGODB_DATABASE', 'openvpn_logs')}")
        print(f"MongoDB Collection: {os.getenv('MONGODB_COLLECTION', 'connection_logs')}")
        print(f"OpenVPN Log Path: {os.getenv('OPENVPN_LOG_PATH', '/var/log/openvpn/openvpn.log')}")
        print(f"OpenVPN Status Path: {os.getenv('OPENVPN_STATUS_PATH', '/var/log/openvpn/status.log')}")
        print(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
        print(f"Log Interval: {os.getenv('LOG_INTERVAL', '60')} seconds")
        print(f"Server Name: {os.getenv('SERVER_NAME', 'openvpn-server-01')}")
        print(f"Server Location: {os.getenv('SERVER_LOCATION', 'us-east-1')}")
        print("===================================")


def create_env_file():
    """Create a .env file from env.example"""
    if os.path.exists('.env'):
        print(".env file already exists. Skipping creation.")
        return
    
    if os.path.exists('env.example'):
        import shutil
        shutil.copy('env.example', '.env')
        print("Created .env file from env.example")
        print("Please edit .env file with your actual configuration values.")
    else:
        print("env.example not found. Creating basic .env file...")
        with open('.env', 'w') as f:
            f.write("""# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/openvpn_logs?retryWrites=true&w=majority
MONGODB_DATABASE=openvpn_logs
MONGODB_COLLECTION=connection_logs

# OpenVPN Configuration
OPENVPN_LOG_PATH=/var/log/openvpn/openvpn.log
OPENVPN_STATUS_PATH=/var/log/openvpn/status.log

# Logging Configuration
LOG_LEVEL=INFO
LOG_INTERVAL=60  # seconds

# Server Configuration
SERVER_NAME=openvpn-server-01
SERVER_LOCATION=us-east-1
""")
        print("Created basic .env file. Please edit with your actual configuration.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            create_env_file()
        elif sys.argv[1] == "validate":
            if Config.validate_config():
                print("Configuration is valid!")
            else:
                sys.exit(1)
        elif sys.argv[1] == "show":
            Config.print_config()
        else:
            print("Usage: python config.py [init|validate|show]")
    else:
        Config.print_config()
        print("\nUse 'python config.py init' to create .env file")
        print("Use 'python config.py validate' to validate configuration")
