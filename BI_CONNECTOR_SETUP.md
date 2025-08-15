# MongoDB BI Connector Setup Guide

This guide helps you connect your OpenVPN Logger MongoDB data to Power BI, Tableau, and other BI tools using ODBC/JDBC connectors.

## Prerequisites

- MongoDB Atlas cluster with your OpenVPN Logger data
- Access to your Atlas connection string
- Power BI Desktop or Tableau Desktop installed

## MongoDB Atlas Setup

### 1. Enable BI Connector (Optional)

If you want to use MongoDB's BI Connector:

1. Go to your MongoDB Atlas dashboard
2. Navigate to your cluster
3. Click "Command Line Tools"
4. Enable "MongoDB BI Connector"
5. Note the connection details provided

### 2. Get Your Connection String

From your Atlas dashboard:
1. Click "Connect"
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your actual password

Example:
```
mongodb+srv://username:yourpassword@cluster.mongodb.net/openvpn_logs?retryWrites=true&w=majority
```

## Power BI Setup

### Method 1: Built-in MongoDB Connector

1. **Open Power BI Desktop**
2. **Get Data** → **MongoDB**
3. **Enter connection details**:
   - Server: `cluster.mongodb.net`
   - Database: `openvpn_logs`
   - Username: Your Atlas username
   - Password: Your Atlas password
4. **Select collections**:
   - `connection_logs` (OpenVPN connection events)
   - `system_stats` (System statistics)

### Method 2: MongoDB ODBC Driver

1. **Download MongoDB ODBC Driver**:
   - Visit: https://www.mongodb.com/try/download/bi-connector
   - Download for your OS (Windows/Linux/macOS)

2. **Install the driver**

3. **In Power BI**:
   - **Get Data** → **ODBC**
   - Select MongoDB ODBC Driver
   - Configure connection string

## Tableau Setup

### Method 1: Built-in MongoDB Connector

1. **Open Tableau Desktop**
2. **Connect** → **MongoDB**
3. **Enter connection details**:
   - Server: `cluster.mongodb.net`
   - Port: `27017` (or leave default)
   - Database: `openvpn_logs`
   - Username: Your Atlas username
   - Password: Your Atlas password

4. **Select collections**:
   - `connection_logs`
   - `system_stats`

### Method 2: MongoDB JDBC Driver

1. **Download MongoDB JDBC Driver**:
   - Visit: https://www.mongodb.com/try/download/bi-connector
   - Download JDBC driver JAR file

2. **In Tableau**:
   - **Connect** → **Other Databases (JDBC)**
   - Driver: MongoDB JDBC Driver
   - URL: `jdbc:mongo://cluster.mongodb.net:27017/openvpn_logs`

## JDBC Connection Setup

### Connection String Format

```
jdbc:mongo://cluster.mongodb.net:27017/openvpn_logs?user=username&password=password
```

### Java Application Example

```java
import java.sql.*;

public class MongoDBJDBC {
    public static void main(String[] args) {
        try {
            // Register JDBC driver
            Class.forName("com.mongodb.jdbc.MongoDriver");
            
            // Open connection
            String url = "jdbc:mongo://cluster.mongodb.net:27017/openvpn_logs?user=username&password=password";
            Connection conn = DriverManager.getConnection(url);
            
            // Execute query
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT * FROM connection_logs LIMIT 10");
            
            // Process results
            while(rs.next()) {
                System.out.println(rs.getString("client_ip"));
            }
            
            conn.close();
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
}
```

## ODBC Connection Setup

### Windows ODBC Setup

1. **Open ODBC Data Source Administrator**
2. **Add new DSN**:
   - Name: `OpenVPN_Logger`
   - Driver: MongoDB ODBC Driver
   - Server: `cluster.mongodb.net`
   - Database: `openvpn_logs`
   - Username: Your Atlas username
   - Password: Your Atlas password

### Connection String Format

```
Driver={MongoDB ODBC Driver};Server=cluster.mongodb.net;Database=openvpn_logs;UID=username;PWD=password;
```

## Data Schema Reference

### Connection Events Collection (`connection_logs`)

| Field | Type | Description |
|-------|------|-------------|
| timestamp | Date | Event timestamp |
| event_type | String | connect, disconnect, auth_failed |
| client_ip | String | Client IP address |
| client_port | Number | Client port |
| username | String | VPN username |
| virtual_ip | String | Assigned virtual IP |
| bytes_received | Number | Bytes received |
| bytes_sent | Number | Bytes sent |
| session_duration | Number | Session duration in seconds |
| server_name | String | Server identifier |
| server_location | String | Server location |

### System Statistics Collection (`system_stats`)

| Field | Type | Description |
|-------|------|-------------|
| timestamp | Date | Stats timestamp |
| type | String | Always "system_stats" |
| stats.cpu_percent | Number | CPU usage percentage |
| stats.memory_percent | Number | Memory usage percentage |
| stats.disk_percent | Number | Disk usage percentage |
| interfaces | Object | Network interface details |

## Sample Queries

### Power BI/Tableau Queries

```sql
-- Recent connections (last 24 hours)
SELECT * FROM connection_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)

-- Top clients by connection count
SELECT client_ip, COUNT(*) as connection_count 
FROM connection_logs 
GROUP BY client_ip 
ORDER BY connection_count DESC

-- System performance over time
SELECT timestamp, stats.cpu_percent, stats.memory_percent 
FROM system_stats 
ORDER BY timestamp DESC
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**:
   - Check firewall settings
   - Verify Atlas IP whitelist
   - Test connection string

2. **Authentication Failed**:
   - Verify username/password
   - Check Atlas user permissions
   - Ensure user has read access

3. **Driver Not Found**:
   - Install correct ODBC/JDBC driver
   - Check driver version compatibility
   - Restart BI application

### Testing Connection

Use MongoDB Compass or mongo shell to test your connection string before configuring BI tools:

```bash
mongosh "mongodb+srv://username:password@cluster.mongodb.net/openvpn_logs"
```

## Support Resources

- [MongoDB BI Connector Documentation](https://docs.mongodb.com/bi-connector/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Power BI MongoDB Connector](https://docs.microsoft.com/en-us/power-bi/connect-data/desktop-connect-mongodb)
- [Tableau MongoDB Connector](https://help.tableau.com/current/pro/desktop/en-us/examples_mongodb.htm)
