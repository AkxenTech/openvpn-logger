# OpenVPN Logger

A comprehensive logging and monitoring system for OpenVPN servers that tracks connection events, system statistics, and provides detailed analytics through MongoDB integration.

## Features

- **Real-time Log Monitoring**: Monitors OpenVPN log files for connection events
- **MongoDB Integration**: Stores connection data and system statistics in MongoDB
- **System Monitoring**: Tracks CPU, memory, disk usage, and network interfaces
- **Event Parsing**: Parses various OpenVPN log events (connect, disconnect, auth failures)
- **Data Analytics**: Provides tools for analyzing connection patterns and statistics
- **Scheduled Monitoring**: Configurable intervals for log processing and system stats
- **IPv4/IPv6 Support**: Handles both IPv4 and IPv6 connection events

## Event Types Tracked

- **connect**: Initial connection attempts
- **authenticated**: Successful authentication with virtual IP assignment
- **disconnect**: Client disconnections
- **auth_failed**: Failed authentication attempts

## Prerequisites

- Python 3.7+
- MongoDB (local or MongoDB Atlas)
- OpenVPN server with logging enabled
- Access to OpenVPN log files

## OpenVPN Configuration

**Important**: Before running the OpenVPN Logger, you must configure your OpenVPN server to write logs to files.

### 1. Edit OpenVPN Server Configuration

Edit your OpenVPN server configuration file (typically `/etc/openvpn/server/server.conf`):

```bash
sudo nano /etc/openvpn/server/server.conf
```

### 2. Add Logging Directives

Add these lines to your OpenVPN server configuration:

```conf
# Logging configuration
log /var/log/openvpn/server.log
status /var/log/openvpn/status.log
verb 3
```

### 3. Create OpenVPN User (if not exists)

The OpenVPN Logger runs as a dedicated user. Create it if it doesn't exist:

```bash
# Create the openvpn user and group
sudo useradd -r -s /bin/false openvpn

# Verify the user was created
id openvpn
```

### 4. Create Log Files

Create the log files with proper permissions:

```bash
# Create log directory if it doesn't exist
sudo mkdir -p /var/log/openvpn

# Create log files
sudo touch /var/log/openvpn/server.log
sudo touch /var/log/openvpn/status.log

# Set proper ownership and permissions
sudo chown root:root /var/log/openvpn/server.log
sudo chown root:root /var/log/openvpn/status.log
sudo chmod 644 /var/log/openvpn/server.log
sudo chmod 644 /var/log/openvpn/status.log

# Create positions file for state persistence
sudo touch /var/log/openvpn/positions.json
sudo chown openvpn:openvpn /var/log/openvpn/positions.json
sudo chmod 644 /var/log/openvpn/positions.json
```

### 5. Restart OpenVPN Server

Restart your OpenVPN server to apply the configuration:

```bash
sudo systemctl restart openvpn-server@server
```

### 6. Verify Logging

Check that logs are being written:

```bash
# Check if logs are being written
sudo tail -f /var/log/openvpn/server.log
sudo tail -f /var/log/openvpn/status.log
```

### 7. Configure Log Rotation

To prevent disk space issues, configure log rotation for OpenVPN logs:

#### Create Logrotate Configuration

Create a logrotate configuration file:

```bash
sudo nano /etc/logrotate.d/openvpn
```

Add the following configuration:

```conf
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
```

#### Log Rotation Settings Explained

- **`daily`**: Rotate logs daily
- **`missingok`**: Don't error if log files are missing
- **`rotate 7`**: Keep 7 rotated log files (1 week)
- **`compress`**: Compress old log files
- **`delaycompress`**: Don't compress the most recent rotated file
- **`notifempty`**: Don't rotate empty files
- **`create 644 root root`**: Create new log files with proper permissions
- **`postrotate`**: Reload OpenVPN service after rotation

#### Install Logrotate (if not available)

If `logrotate` is not installed:

```bash
# Install logrotate
sudo apt-get update
sudo apt-get install -y logrotate

# Verify installation
logrotate --version
```

#### Test Log Rotation

Test the configuration:

```bash
# Test logrotate configuration
sudo logrotate -d /etc/logrotate.d/openvpn

# Force rotation (for testing)
sudo logrotate -f /etc/logrotate.d/openvpn
```

### 8. Monitor Disk Usage

Set up monitoring to prevent disk space issues:

```bash
# Check current log sizes
sudo du -sh /var/log/openvpn/

# Monitor disk usage
df -h /var/log/

# Check logrotate status
sudo logrotate -d /etc/logrotate.d/openvpn
```

### 9. Positions File Management

The `positions.json` file tracks processed log positions and notified sessions to prevent duplicates. This file can grow over time and should be managed:

#### Monitor Positions File Size

```bash
# Check positions file size
ls -lh /var/log/openvpn/positions.json

# View current tracked sessions count
jq '.notified_sessions | length' /var/log/openvpn/positions.json
```

#### Clean Up Old Sessions (Optional)

If the positions file becomes too large, you can clean old sessions:

```bash
# Backup current positions
sudo cp /var/log/openvpn/positions.json /var/log/openvpn/positions.json.backup

# Remove sessions older than 30 days (keeps recent positions)
sudo jq 'del(.notified_sessions[] | select(test(".*:.*:.*") | not))' /var/log/openvpn/positions.json > /tmp/cleaned_positions.json
sudo mv /tmp/cleaned_positions.json /var/log/openvpn/positions.json
sudo chown openvpn:openvpn /var/log/openvpn/positions.json
```

#### Automatic Cleanup Script

Create a cleanup script to run periodically:

```bash
sudo nano /usr/local/bin/cleanup-openvpn-positions.sh
```

Add this content:

```bash
#!/bin/bash
# Clean up old positions file entries

POSITIONS_FILE="/var/log/openvpn/positions.json"
MAX_SESSIONS=1000

if [ -f "$POSITIONS_FILE" ]; then
    # Get current session count
    SESSION_COUNT=$(jq '.notified_sessions | length' "$POSITIONS_FILE" 2>/dev/null || echo "0")
    
    if [ "$SESSION_COUNT" -gt "$MAX_SESSIONS" ]; then
        # Keep only the most recent sessions
        jq --arg max "$MAX_SESSIONS" '.notified_sessions = (.notified_sessions | .[-($max|tonumber):])' "$POSITIONS_FILE" > /tmp/cleaned_positions.json
        mv /tmp/cleaned_positions.json "$POSITIONS_FILE"
        chown openvpn:openvpn "$POSITIONS_FILE"
        echo "$(date): Cleaned positions file, reduced from $SESSION_COUNT to $MAX_SESSIONS sessions"
    fi
fi
```

Make it executable and add to crontab:

```bash
sudo chmod +x /usr/local/bin/cleanup-openvpn-positions.sh

# Add to crontab to run daily at 2 AM
sudo crontab -e
# Add this line:
# 0 2 * * * /usr/local/bin/cleanup-openvpn-positions.sh
```

## Installation

### Quick Setup (Recommended)

For new deployments, use the automated installation script:

```bash
# Clone the repository
git clone <repository-url>
cd openvpn-logger

# Run the installation script
./install.sh
```

The script will:
- Install system dependencies
- Create the openvpn user
- Set up Python virtual environment
- Configure log rotation
- Create systemd service
- Set up proper file permissions

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd openvpn-logger
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**:
   ```bash
   python config.py init
   ```

4. **Edit the `.env` file** with your actual configuration:
   ```bash
   nano .env
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/openvpn_logs?retryWrites=true&w=majority
MONGODB_DATABASE=openvpn_logs
MONGODB_COLLECTION=connection_logs

# OpenVPN Configuration
OPENVPN_LOG_PATH=/var/log/openvpn/server.log
OPENVPN_STATUS_PATH=/var/log/openvpn/status.log

# State Persistence (for preventing duplicate events)
POSITIONS_FILE=/var/log/openvpn/positions.json
# Maximum number of tracked sessions to prevent memory bloat (default: 1000)
MAX_TRACKED_SESSIONS=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_INTERVAL=60  # seconds

# Server Configuration
SERVER_NAME=openvpn-server-01
SERVER_LOCATION=us-east-1
```

**Note**: Server configuration is centralized through the `Config.get_server_config()` function, ensuring consistent usage across all components with environment variable fallbacks.

### MongoDB Setup

1. **Local MongoDB**:
   ```bash
   # Install MongoDB
   sudo apt-get install mongodb
   
   # Start MongoDB service
   sudo systemctl start mongodb
   ```

2. **MongoDB Atlas** (Recommended):
   - Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Get your connection string
   - Update `MONGODB_URI` in your `.env` file

## Usage

### Starting the Logger

```bash
# Start the OpenVPN logger
python openvpn_logger.py
```

The logger will:
- Monitor OpenVPN log files for new events
- Parse and store connection events in MongoDB
- Log system statistics every 5 minutes
- Run continuously until stopped (Ctrl+C)

### Configuration Management

```bash
# Initialize configuration
python config.py init

# Validate configuration
python config.py validate

# Show current configuration
python config.py show
```

### Data Analysis

The `analyzer.py` script provides various analysis tools:

```bash
# Show connection summary (last 24 hours)
python analyzer.py

# Show top clients
python analyzer.py --top-clients

# Show recent timeline
python analyzer.py --timeline

# Show hourly statistics
python analyzer.py --hourly

# Show system statistics
python analyzer.py --system

# Search for specific client
python analyzer.py --client 192.168.1.100

# Custom time range (48 hours)
python analyzer.py --hours 48
```

## OpenVPN Log Format Support

The logger parses standard OpenVPN log formats:

```
2024-01-01 12:00:00 Peer Connection Initiated with [AF_INET]192.168.1.100:12345
2024-01-01 12:00:01 192.168.1.100:12345 MULTI: Learn: 10.8.0.2
2024-01-01 12:00:02 192.168.1.100:12345 MULTI: primary virtual IP 10.8.0.2
2024-01-01 12:00:03 192.168.1.100:12345 AUTH: Failed
```

## Data Schema

### Connection Events

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event_type": "connect",
  "client_ip": "192.168.1.100",
  "client_port": 12345,
  "username": "user123",
  "virtual_ip": "10.8.0.2",
  "bytes_received": 1024,
  "bytes_sent": 2048,
  "session_duration": 3600,
  "server_name": "openvpn-server-01",
  "server_location": "us-east-1",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### System Statistics

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "type": "system_stats",
  "stats": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_available": 8589934592,
    "disk_percent": 67.3,
    "disk_free": 107374182400
  },
  "interfaces": {
    "eth0": {
      "ip": "192.168.1.10",
      "netmask": "255.255.255.0"
    }
  },
  "server_name": "openvpn-server-01",
  "server_location": "us-east-1"
}
```

## Monitoring and Alerts

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems

### Common Issues

1. **MongoDB Connection Failed**:
   - Check your `MONGODB_URI` in the `.env` file
   - Ensure MongoDB is running
   - Verify network connectivity

2. **OpenVPN Log File Not Found**:
   - Check `OPENVPN_LOG_PATH` in your `.env` file
   - Ensure the file exists and is readable
   - Verify OpenVPN logging is enabled

3. **Permission Denied**:
   - Ensure the script has read access to OpenVPN log files
   - Run with appropriate permissions if needed

4. **User Creation Issues**:
   - **Error**: `chown: invalid user: 'openvpn:openvpn'`
   - **Solution**: Create the openvpn user first:
     ```bash
     sudo useradd -r -s /bin/false openvpn
     id openvpn  # Verify user exists
     ```
   - **Error**: `useradd: user 'openvpn' already exists`
   - **Solution**: User already exists, proceed with installation

5. **Service Won't Start**:
   - Check if the openvpn user exists: `id openvpn`
   - Verify file permissions: `ls -la /opt/openvpn-logger/`
   - Check service logs: `sudo journalctl -u openvpn-logger -f`

6. **Package Repository Errors**:
   - **Error**: `The repository 'file:/cdrom jammy Release' no longer has a Release file`
   - **Solution**: Remove stale CD-ROM repository entries:
     ```bash
     sudo sed -i '/^deb cdrom:/d' /etc/apt/sources.list
     sudo apt-get clean
     sudo apt-get update
     ```
   - **Alternative**: The install script now automatically fixes this issue

## Security Considerations

- Store sensitive configuration in environment variables
- Use MongoDB Atlas with proper authentication
- Restrict access to log files and configuration
- Regularly rotate log files
- Monitor for suspicious connection patterns

## Performance Optimization

- Adjust `LOG_INTERVAL` based on your needs (default: 60 seconds)
- Use MongoDB indexes for better query performance
- Consider log rotation to prevent large log files
- Monitor system resources during operation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the configuration examples
- Open an issue on GitHub

## Changelog

### v1.0.0
- Initial release
- Basic OpenVPN log parsing
- MongoDB integration
- System monitoring
- Data analysis tools
