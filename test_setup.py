#!/usr/bin/env python3
"""
Test script for OpenVPN Logger setup verification
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import pymongo
        print("✓ pymongo imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pymongo: {e}")
        return False
    
    try:
        import schedule
        print("✓ schedule imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import schedule: {e}")
        return False
    
    try:
        import psutil
        print("✓ psutil imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import psutil: {e}")
        return False
    
    try:
        import netifaces
        print("✓ netifaces imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import netifaces: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-dotenv: {e}")
        return False
    
    return True

def test_config_files():
    """Test if configuration files exist"""
    print("\nTesting configuration files...")
    
    files_to_check = [
        'openvpn_logger.py',
        'config.py',
        'analyzer.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for file in files_to_check:
        if Path(file).exists():
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_exist = False
    
    return all_exist

def test_env_file():
    """Test environment file setup"""
    print("\nTesting environment configuration...")
    
    if Path('.env').exists():
        print("✓ .env file exists")
        
        # Load and check environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['MONGODB_URI']
        optional_vars = [
            'MONGODB_DATABASE', 'MONGODB_COLLECTION',
            'OPENVPN_LOG_PATH', 'OPENVPN_STATUS_PATH',
            'LOG_LEVEL', 'LOG_INTERVAL',
            'SERVER_NAME', 'SERVER_LOCATION'
        ]
        
        missing_required = []
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        if missing_required:
            print(f"✗ Missing required environment variables: {', '.join(missing_required)}")
            return False
        else:
            print("✓ All required environment variables are set")
        
        # Check optional variables
        for var in optional_vars:
            if os.getenv(var):
                print(f"✓ {var} is set")
            else:
                print(f"⚠ {var} is not set (using default)")
        
        return True
    else:
        print("✗ .env file not found")
        print("Run 'python config.py init' to create it")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\nTesting MongoDB connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        uri = os.getenv('MONGODB_URI')
        if not uri:
            print("✗ MONGODB_URI not set")
            return False
        
        import pymongo
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ MongoDB connection successful")
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False

def test_openvpn_log_path():
    """Test OpenVPN log path accessibility"""
    print("\nTesting OpenVPN log path...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    log_path = os.getenv('OPENVPN_LOG_PATH', '/var/log/openvpn/openvpn.log')
    path = Path(log_path)
    
    if path.exists():
        print(f"✓ OpenVPN log file exists: {log_path}")
        
        # Test read access
        try:
            with open(path, 'r') as f:
                f.read(1)  # Try to read one character
            print("✓ OpenVPN log file is readable")
            return True
        except PermissionError:
            print(f"✗ Permission denied reading {log_path}")
            return False
        except Exception as e:
            print(f"✗ Error reading log file: {e}")
            return False
    else:
        print(f"⚠ OpenVPN log file not found: {log_path}")
        print("This is normal if OpenVPN is not running or logs are in a different location")
        return True  # Not a critical error

def test_system_monitoring():
    """Test system monitoring capabilities"""
    print("\nTesting system monitoring...")
    
    try:
        import psutil
        import netifaces
        
        # Test CPU monitoring
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"✓ CPU monitoring: {cpu_percent}%")
        
        # Test memory monitoring
        memory = psutil.virtual_memory()
        print(f"✓ Memory monitoring: {memory.percent}% used")
        
        # Test disk monitoring
        disk = psutil.disk_usage('/')
        print(f"✓ Disk monitoring: {disk.percent}% used")
        
        # Test network interfaces
        interfaces = netifaces.interfaces()
        print(f"✓ Network interfaces: {len(interfaces)} found")
        
        return True
        
    except Exception as e:
        print(f"✗ System monitoring test failed: {e}")
        return False

def test_push_notifications():
    """Test push notification configuration"""
    print("\nTesting push notifications...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if push notification variables are set
        pushover_vars = [
            'PUSHOVER_API_TOKEN',
            'PUSHOVER_USER_KEY',
            'PUSHOVER_DEVICE'
        ]
        
        configured_vars = []
        for var in pushover_vars:
            if os.getenv(var):
                configured_vars.append(var)
        
        if configured_vars:
            print(f"✓ Push notification configured: {len(configured_vars)}/{len(pushover_vars)} variables set")
            
            # Test notification manager import
            try:
                from notifications import NotificationManager
                print("✓ Notification manager imported successfully")
                
                # Test notification manager initialization
                try:
                    notification_manager = NotificationManager()
                    print("✓ Notification manager initialized successfully")
                    
                    # Ask user if they want to send a test notification
                    print("\nSend test notification? (y/N): ", end="")
                    try:
                        response = input().strip().lower()
                        if response in ['y', 'yes']:
                            # Test sending a sample notification
                            test_message = "OpenVPN Logger test notification - Setup verification successful"
                            print("Sending test notification...")
                            try:
                                result = notification_manager.send_notification(
                                    title="OpenVPN Logger Test",
                                    message=test_message,
                                    priority=0  # Normal priority for test
                                )
                                if result:
                                    print("✓ Test notification sent successfully")
                                    print("  Check your device for the notification")
                                else:
                                    print("⚠ Test notification failed to send")
                                return True
                            except Exception as e:
                                print(f"⚠ Test notification failed: {e}")
                                return True  # Not critical for basic functionality
                        else:
                            print("✓ Skipped test notification")
                            return True
                    except (EOFError, KeyboardInterrupt):
                        print("\n✓ Skipped test notification")
                        return True
                    
                except Exception as e:
                    print(f"⚠ Notification manager initialization failed: {e}")
                    return True  # Not critical for basic functionality
                    
            except ImportError as e:
                print(f"⚠ Notification manager import failed: {e}")
                return True  # Not critical for basic functionality
                
        else:
            print("⚠ Push notifications not configured (optional)")
            print("  Set PUSHOVER_API_TOKEN, PUSHOVER_USER_KEY, and PUSHOVER_DEVICE in .env for notifications")
            return True  # Not critical for basic functionality
            
    except Exception as e:
        print(f"⚠ Push notification test failed: {e}")
        return True  # Not critical for basic functionality

def main():
    """Run all tests"""
    print("=== OpenVPN Logger Setup Test ===\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Files", test_config_files),
        ("Environment Configuration", test_env_file),
        ("MongoDB Connection", test_mongodb_connection),
        ("OpenVPN Log Path", test_openvpn_log_path),
        ("System Monitoring", test_system_monitoring),
        ("Push Notifications", test_push_notifications)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        print()
    
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your OpenVPN Logger is ready to use.")
        print("\nTo start the logger:")
        print("  python openvpn_logger.py")
        print("\nTo analyze data:")
        print("  python analyzer.py")
    else:
        print("⚠ Some tests failed. Please check the configuration.")
        print("\nCommon fixes:")
        print("1. Run 'python config.py init' to create .env file")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Configure MongoDB connection in .env file")
        print("4. Ensure OpenVPN log files are accessible")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
