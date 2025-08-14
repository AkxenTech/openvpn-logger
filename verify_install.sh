#!/bin/bash

# OpenVPN Logger Installation Verification Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "OpenVPN Logger Installation Verification"
echo "========================================"
echo ""

# Check 1: Service file exists
if [ -f "/etc/systemd/system/openvpn-logger.service" ]; then
    print_status "Systemd service file exists"
else
    print_error "Systemd service file not found"
fi

# Check 2: OpenVPN user exists
if id "openvpn" &>/dev/null; then
    print_status "OpenVPN user exists"
else
    print_error "OpenVPN user not found"
fi

# Check 3: Installation directory exists
if [ -d "/opt/openvpn-logger" ]; then
    print_status "Installation directory exists"
    echo "  Contents: $(ls /opt/openvpn-logger/ | wc -l) files"
else
    print_error "Installation directory not found"
fi

# Check 4: Virtual environment exists
if [ -d "/opt/openvpn-logger/venv" ]; then
    print_status "Python virtual environment exists"
else
    print_error "Python virtual environment not found"
fi

# Check 5: Configuration file exists
if [ -f "/opt/openvpn-logger/.env" ]; then
    print_status "Configuration file (.env) exists"
    echo "  Configuration preview:"
    head -5 /opt/openvpn-logger/.env | sed 's/^/    /'
else
    print_error "Configuration file (.env) not found"
fi

# Check 6: Service status
echo ""
echo "Service Status:"
if systemctl is-active --quiet openvpn-logger; then
    print_status "Service is running"
elif systemctl is-enabled --quiet openvpn-logger; then
    print_warning "Service is enabled but not running"
else
    print_warning "Service is not enabled"
fi

# Check 7: Test configuration
echo ""
echo "Configuration Test:"
cd /opt/openvpn-logger
if python3 config.py validate 2>/dev/null; then
    print_status "Configuration validation passed"
else
    print_error "Configuration validation failed"
fi

# Check 8: MongoDB connection test
echo ""
echo "MongoDB Connection Test:"
if python3 test_setup.py 2>/dev/null; then
    print_status "MongoDB connection test passed"
else
    print_warning "MongoDB connection test failed (check your MONGODB_URI in .env)"
fi

# Check 9: Recent logs
echo ""
echo "Recent Service Logs:"
if journalctl -u openvpn-logger -n 3 --no-pager 2>/dev/null | grep -q .; then
    print_status "Service logs found"
    journalctl -u openvpn-logger -n 3 --no-pager | sed 's/^/  /'
else
    print_warning "No recent service logs found"
fi

echo ""
echo "Verification Complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/openvpn-logger/.env with your actual configuration"
echo "2. Start the service: sudo systemctl start openvpn-logger"
echo "3. Enable on boot: sudo systemctl enable openvpn-logger"
echo "4. Monitor logs: sudo journalctl -u openvpn-logger -f"
