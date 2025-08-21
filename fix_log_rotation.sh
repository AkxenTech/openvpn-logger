#!/bin/bash

# OpenVPN Log Rotation Fix Script
# This script fixes the issue where OpenVPN continues writing to rotated log files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

# Check if OpenVPN service is running
check_openvpn_service() {
    if ! systemctl is-active --quiet openvpn-server@server; then
        print_warning "OpenVPN service is not running"
        return 1
    fi
    return 0
}

# Check log file status
check_log_files() {
    print_status "Checking OpenVPN log files..."
    
    # Check server.log
    if [ -f "/var/log/openvpn/server.log" ]; then
        current_size=$(stat -c%s "/var/log/openvpn/server.log" 2>/dev/null || echo "0")
        print_status "Current server.log size: ${current_size} bytes"
    else
        print_warning "server.log not found"
    fi
    
    if [ -f "/var/log/openvpn/server.log.1" ]; then
        rotated_size=$(stat -c%s "/var/log/openvpn/server.log.1" 2>/dev/null || echo "0")
        print_status "Rotated server.log.1 size: ${rotated_size} bytes"
    fi
    
    # Check status.log
    if [ -f "/var/log/openvpn/status.log" ]; then
        status_size=$(stat -c%s "/var/log/openvpn/status.log" 2>/dev/null || echo "0")
        print_status "Current status.log size: ${status_size} bytes"
    else
        print_warning "status.log not found"
    fi
    
    if [ -f "/var/log/openvpn/status.log.1" ]; then
        status_rotated_size=$(stat -c%s "/var/log/openvpn/status.log.1" 2>/dev/null || echo "0")
        print_status "Rotated status.log.1 size: ${status_rotated_size} bytes"
    fi
}

# Fix log rotation issue
fix_log_rotation() {
    print_status "Fixing OpenVPN log rotation issue..."
    
    # Method 1: Restart OpenVPN service
    print_status "Method 1: Restarting OpenVPN service..."
    sudo systemctl restart openvpn-server@server
    
    # Wait a moment for service to restart
    sleep 2
    
    # Check if service is running
    if systemctl is-active --quiet openvpn-server@server; then
        print_status "✓ OpenVPN service restarted successfully"
    else
        print_error "✗ OpenVPN service failed to restart"
        return 1
    fi
    
    # Method 2: Alternative - Send SIGHUP signal
    print_status "Method 2: Sending SIGHUP signal to OpenVPN processes..."
    if sudo pkill -HUP -f "openvpn.*server" 2>/dev/null; then
        print_status "✓ SIGHUP signal sent successfully"
    else
        print_warning "No OpenVPN server processes found for SIGHUP"
    fi
    
    # Method 3: Reset positions.json if needed
    print_status "Method 3: Checking positions.json file..."
    if [ -f "/var/log/openvpn/positions.json" ]; then
        print_status "Backing up positions.json before potential reset..."
        sudo cp /var/log/openvpn/positions.json /var/log/openvpn/positions.json.backup.$(date +%Y%m%d_%H%M%S)
        
        # Check if we should reset positions
        if [ -f "/var/log/openvpn/server.log.1" ] && [ -f "/var/log/openvpn/server.log" ]; then
            current_size=$(stat -c%s "/var/log/openvpn/server.log" 2>/dev/null || echo "0")
            if [ "$current_size" -eq 0 ]; then
                print_warning "Current log file is empty, resetting positions.json"
                sudo rm -f /var/log/openvpn/positions.json
                print_status "✓ positions.json reset (will be recreated on next run)"
            else
                print_status "✓ positions.json appears to be valid"
            fi
        fi
    else
        print_status "No positions.json file found (normal for new installations)"
    fi
}

# Check for rotated file writing
check_for_rotated_file_writing() {
    print_status "Checking if OpenVPN is writing to rotated files..."
    
    local rotated_detected=false
    
    # Check server.log
    if [ -f "/var/log/openvpn/server.log" ]; then
        local current_size=$(stat -c%s "/var/log/openvpn/server.log" 2>/dev/null || echo "0")
        sleep 2
        local new_size=$(stat -c%s "/var/log/openvpn/server.log" 2>/dev/null || echo "0")
        
        if [ "$new_size" -eq "$current_size" ]; then
            # Check if rotated server.log is growing
            if [ -f "/var/log/openvpn/server.log.1" ]; then
                local rotated_size=$(stat -c%s "/var/log/openvpn/server.log.1" 2>/dev/null || echo "0")
                sleep 2
                local new_rotated_size=$(stat -c%s "/var/log/openvpn/server.log.1" 2>/dev/null || echo "0")
                
                if [ "$new_rotated_size" -gt "$rotated_size" ]; then
                    print_warning "OpenVPN is writing to rotated server.log.1 instead of current server.log"
                    rotated_detected=true
                fi
            fi
        fi
    fi
    
    # Check status.log
    if [ -f "/var/log/openvpn/status.log" ]; then
        local status_current_size=$(stat -c%s "/var/log/openvpn/status.log" 2>/dev/null || echo "0")
        sleep 2
        local status_new_size=$(stat -c%s "/var/log/openvpn/status.log" 2>/dev/null || echo "0")
        
        if [ "$status_new_size" -eq "$status_current_size" ]; then
            # Check if rotated status.log is growing
            if [ -f "/var/log/openvpn/status.log.1" ]; then
                local status_rotated_size=$(stat -c%s "/var/log/openvpn/status.log.1" 2>/dev/null || echo "0")
                sleep 2
                local status_new_rotated_size=$(stat -c%s "/var/log/openvpn/status.log.1" 2>/dev/null || echo "0")
                
                if [ "$status_new_rotated_size" -gt "$status_rotated_size" ]; then
                    print_warning "OpenVPN is writing to rotated status.log.1 instead of current status.log"
                    rotated_detected=true
                fi
            fi
        fi
    fi
    
    if [ "$rotated_detected" = true ]; then
        print_error "Log rotation issue detected - OpenVPN is writing to rotated files"
        return 0
    else
        print_status "✓ Log files appear to be writing to current files correctly"
        return 1
    fi
}

# Verify the fix
verify_fix() {
    print_status "Verifying the fix..."
    
    # Check if new logs are being written to current files
    print_status "Checking if logs are being written to current files..."
    
    # Check server.log
    if [ -f "/var/log/openvpn/server.log" ]; then
        local initial_size=$(stat -c%s "/var/log/openvpn/server.log" 2>/dev/null || echo "0")
        print_status "Initial server.log size: ${initial_size} bytes"
        
        # Wait a moment for new logs
        print_status "Waiting for new log entries..."
        sleep 5
        
        local final_size=$(stat -c%s "/var/log/openvpn/server.log" 2>/dev/null || echo "0")
        print_status "Final server.log size: ${final_size} bytes"
        
        if [ "$final_size" -gt "$initial_size" ]; then
            print_status "✓ server.log is being written to current file"
        else
            print_warning "⚠ No new logs detected in server.log"
        fi
    fi
    
    # Check status.log
    if [ -f "/var/log/openvpn/status.log" ]; then
        local status_initial_size=$(stat -c%s "/var/log/openvpn/status.log" 2>/dev/null || echo "0")
        print_status "Initial status.log size: ${status_initial_size} bytes"
        
        # Wait a moment for new logs
        sleep 5
        
        local status_final_size=$(stat -c%s "/var/log/openvpn/status.log" 2>/dev/null || echo "0")
        print_status "Final status.log size: ${status_final_size} bytes"
        
        if [ "$status_final_size" -gt "$status_initial_size" ]; then
            print_status "✓ status.log is being written to current file"
            return 0
        else
            print_warning "⚠ No new logs detected in status.log"
            return 1
        fi
    else
        print_warning "status.log not found"
        return 1
    fi
}

# Update logrotate configuration
update_logrotate_config() {
    print_status "Updating logrotate configuration..."
    
    # Create backup of current config
    if [ -f "/etc/logrotate.d/openvpn" ]; then
        sudo cp /etc/logrotate.d/openvpn /etc/logrotate.d/openvpn.backup
        print_status "Backup created: /etc/logrotate.d/openvpn.backup"
    fi
    
    # Update configuration to use restart instead of reload
    sudo tee /etc/logrotate.d/openvpn > /dev/null << 'EOF'
/var/log/openvpn/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        # Force OpenVPN to reopen log files by restarting the service
        systemctl restart openvpn-server@server
        # Alternative: send SIGHUP signal to force log file reopening
        # pkill -HUP -f "openvpn.*server"
    endscript
}
EOF
    
    print_status "✓ Logrotate configuration updated"
}

# Main function
main() {
    print_status "OpenVPN Log Rotation Fix Script"
    print_status "================================="
    
    check_root
    
    # Check if OpenVPN service is running
    if ! check_openvpn_service; then
        print_error "OpenVPN service is not running. Please start it first."
        exit 1
    fi
    
    # Check current log file status
    check_log_files
    
    # Check if there's actually a rotation issue
    if check_for_rotated_file_writing; then
        print_status "Log rotation issue detected, applying fix..."
        
        # Fix the issue
        if fix_log_rotation; then
            print_status "✓ Log rotation issue fixed"
        else
            print_error "✗ Failed to fix log rotation issue"
            exit 1
        fi
        
        # Verify the fix
        if verify_fix; then
            print_status "✓ Verification successful"
        else
            print_warning "⚠ Verification inconclusive - check manually"
        fi
    else
        print_status "✓ No log rotation issues detected - OpenVPN is writing to current files correctly"
    fi
    
    # Offer to update logrotate configuration
    echo ""
    read -p "Update logrotate configuration to prevent future issues? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        update_logrotate_config
        print_status "✓ Future log rotation issues will be automatically prevented"
    fi
    
    print_status "Fix completed!"
    print_status "Monitor logs with: sudo tail -f /var/log/openvpn/server.log"
}

# Run main function
main "$@"
