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

## Installation

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
OPENVPN_LOG_PATH=/var/log/openvpn/openvpn.log
OPENVPN_STATUS_PATH=/var/log/openvpn/status.log

# Logging Configuration
LOG_LEVEL=INFO
LOG_INTERVAL=60  # seconds

# Server Configuration
SERVER_NAME=openvpn-server-01
SERVER_LOCATION=us-east-1
```

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
