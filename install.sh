#!/bin/bash

# OpenVPN Logger Installation Script
# This script sets up the OpenVPN Logger on a Linux system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.7"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python 3.7 or higher is required. Found: $python_version"
        exit 1
    fi
    
    print_status "Python $python_version found"
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        # Fix stale CD-ROM repository issue
        print_status "Fixing package repository sources..."
        sudo sed -i '/^deb cdrom:/d' /etc/apt/sources.list
        sudo sed -i '/^deb-src cdrom:/d' /etc/apt/sources.list
        sudo sed -i '/^deb file:\/cdrom/d' /etc/apt/sources.list
        sudo sed -i '/^deb-src file:\/cdrom/d' /etc/apt/sources.list
        sudo apt-get clean
        
        sudo apt-get update
        sudo apt-get install -y python3-pip python3-venv curl gnupg logrotate
        
        # Ask user about MongoDB setup
        echo ""
        echo "MongoDB Setup Options:"
        echo "1) Use MongoDB Atlas (cloud.mongodb.com) - Recommended"
        echo "2) Install local MongoDB Community Edition"
        echo "3) Skip MongoDB installation (install manually later)"
        read -p "Choose option (1-3): " mongodb_choice
        
        case $mongodb_choice in
            1)
                print_status "Using MongoDB Atlas - no local MongoDB installation needed"
                print_status "Make sure to update MONGODB_URI in your .env file with your Atlas connection string"
                ;;
            2)
                print_status "Installing MongoDB Community Edition locally..."
                
                # Import MongoDB public GPG key
                curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
                    sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
                    --dearmor
                    
                # Create list file for MongoDB
                echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
                    sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
                    
                # Update package database and install MongoDB
                sudo apt-get update
                sudo apt-get install -y mongodb-org
                
                # Start and enable MongoDB service
                sudo systemctl start mongod
                sudo systemctl enable mongod
                
                print_status "MongoDB installed and started locally"
                ;;
            3)
                print_warning "Skipping MongoDB installation. You'll need to install it manually later."
                ;;
            *)
                print_warning "Invalid choice. Assuming MongoDB Atlas usage."
                ;;
        esac
        
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3-pip mongodb-org
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y python3-pip mongodb-org
    else
        print_warning "Could not detect package manager. Please install Python 3 and MongoDB manually."
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    print_status "Virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Python dependencies installed"
}

# Setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
            print_status "Created .env file from env.example"
            
            # Provide guidance for MongoDB Atlas users
            echo ""
            print_status "Configuration file created!"
            print_warning "IMPORTANT: You need to edit the .env file with your actual configuration:"
            echo ""
            echo "For MongoDB Atlas users:"
            echo "1. Get your connection string from cloud.mongodb.com"
            echo "2. Update MONGODB_URI in .env file"
            echo "3. Update SERVER_NAME and SERVER_LOCATION"
            echo "4. Verify OPENVPN_LOG_PATH points to your actual log file"
            echo ""
            echo "Example MongoDB Atlas URI:"
            echo "MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/openvpn_logs?retryWrites=true&w=majority"
            echo ""
        else
            print_warning "env.example not found. Creating basic .env file..."
            cat > .env << EOF
# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/openvpn_logs?retryWrites=true&w=majority
MONGODB_DATABASE=openvpn_logs
MONGODB_COLLECTION=connection_logs

# OpenVPN Configuration
OPENVPN_LOG_PATH=/var/log/openvpn/server.log
OPENVPN_STATUS_PATH=/var/log/openvpn/status.log

# State Persistence (for preventing duplicate events)
POSITIONS_FILE=/var/log/openvpn/positions.json
MAX_TRACKED_SESSIONS=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_INTERVAL=60  # seconds

# Server Configuration
SERVER_NAME=openvpn-server-01
SERVER_LOCATION=us-east-1
EOF
            print_status "Created basic .env file"
        fi
    else
        print_status ".env file already exists"
    fi
}

# Setup log rotation
setup_log_rotation() {
    print_status "Setting up log rotation..."
    
    # Create logrotate configuration for OpenVPN logs
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
        systemctl reload openvpn-server@server
    endscript
}
EOF
    
    print_status "Log rotation configured for OpenVPN logs"
    print_status "Logs will be rotated daily and kept for 7 days"
}

# Create systemd service
setup_systemd() {
    print_status "Setting up systemd service..."
    
    # Create openvpn user if it doesn't exist
    if ! id "openvpn" &>/dev/null; then
        sudo useradd -r -s /bin/false openvpn
        print_status "Created openvpn user"
    fi
    
    # Copy files to /opt/openvpn-logger
    sudo mkdir -p /opt/openvpn-logger
    sudo cp -r . /opt/openvpn-logger/
    sudo chown -R openvpn:openvpn /opt/openvpn-logger
    
    # Copy systemd service file
    sudo cp openvpn-logger.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    print_status "Systemd service created"
    print_status "To start the service: sudo systemctl start openvpn-logger"
    print_status "To enable on boot: sudo systemctl enable openvpn-logger"
}

# Test configuration
test_config() {
    print_status "Testing configuration..."
    source venv/bin/activate
    python3 config.py validate
}

# Main installation function
main() {
    print_status "Starting OpenVPN Logger installation..."
    
    check_root
    check_python
    install_system_deps
    create_venv
    install_python_deps
    setup_config
    setup_log_rotation
    setup_systemd
    test_config
    
    print_status "Installation completed successfully!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Edit /opt/openvpn-logger/.env with your actual configuration"
    print_status "2. Start the service: sudo systemctl start openvpn-logger"
    print_status "3. Enable on boot: sudo systemctl enable openvpn-logger"
    print_status "4. Check status: sudo systemctl status openvpn-logger"
    print_status "5. View logs: sudo journalctl -u openvpn-logger -f"
    print_status ""
    print_status "For data analysis, use: python3 analyzer.py"
}

# Run main function
main "$@"
