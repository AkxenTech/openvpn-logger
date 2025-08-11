#!/usr/bin/env python3
"""
OpenVPN Logger Data Analyzer
Provides utilities to query and analyze connection logs from MongoDB
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import argparse

import pymongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenVPNAnalyzer:
    """Analyzes OpenVPN connection logs from MongoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            uri = os.getenv('MONGODB_URI')
            database = os.getenv('MONGODB_DATABASE', 'openvpn_logs')
            collection = os.getenv('MONGODB_COLLECTION', 'connection_logs')
            
            if not uri:
                print("Error: MONGODB_URI not set in environment variables")
                sys.exit(1)
            
            self.client = pymongo.MongoClient(uri)
            self.db = self.client[database]
            self.collection = self.db[collection]
            
            # Test connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB")
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            sys.exit(1)
    
    def get_connection_summary(self, hours: int = 24) -> Dict:
        """Get a summary of connections for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff_time}}},
            {'$group': {
                '_id': '$event_type',
                'count': {'$sum': 1},
                'unique_clients': {'$addToSet': '$client_ip'}
            }},
            {'$project': {
                'event_type': '$_id',
                'count': 1,
                'unique_clients': {'$size': '$unique_clients'}
            }}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        summary = {}
        
        for result in results:
            summary[result['event_type']] = {
                'count': result['count'],
                'unique_clients': result['unique_clients']
            }
        
        return summary
    
    def get_top_clients(self, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Get top clients by connection count"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff_time}}},
            {'$group': {
                '_id': '$client_ip',
                'total_connections': {'$sum': 1},
                'connect_events': {
                    '$sum': {'$cond': [{'$eq': ['$event_type', 'connect']}, 1, 0]}
                },
                'disconnect_events': {
                    '$sum': {'$cond': [{'$eq': ['$event_type', 'disconnect']}, 1, 0]}
                },
                'auth_failures': {
                    '$sum': {'$cond': [{'$eq': ['$event_type', 'auth_failed']}, 1, 0]}
                },
                'last_seen': {'$max': '$timestamp'}
            }},
            {'$sort': {'total_connections': -1}},
            {'$limit': limit}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def get_connection_timeline(self, hours: int = 24) -> List[Dict]:
        """Get connection events timeline"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff_time}}},
            {'$sort': {'timestamp': -1}},
            {'$limit': 100}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def get_hourly_stats(self, hours: int = 24) -> List[Dict]:
        """Get hourly connection statistics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff_time}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$timestamp'},
                    'month': {'$month': '$timestamp'},
                    'day': {'$dayOfMonth': '$timestamp'},
                    'hour': {'$hour': '$timestamp'}
                },
                'total_events': {'$sum': 1},
                'connect_events': {
                    '$sum': {'$cond': [{'$eq': ['$event_type', 'connect']}, 1, 0]}
                },
                'disconnect_events': {
                    '$sum': {'$cond': [{'$eq': ['$event_type', 'disconnect']}, 1, 0]}
                },
                'auth_failures': {
                    '$sum': {'$cond': [{'$eq': ['$event_type', 'auth_failed']}, 1, 0]}
                }
            }},
            {'$sort': {'_id': 1}}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def search_by_client_ip(self, client_ip: str, hours: int = 168) -> List[Dict]:
        """Search for events by client IP address"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = {
            'client_ip': client_ip,
            'timestamp': {'$gte': cutoff_time}
        }
        
        return list(self.collection.find(query).sort('timestamp', -1))
    
    def get_system_stats(self, hours: int = 24) -> List[Dict]:
        """Get system statistics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = {
            'type': 'system_stats',
            'timestamp': {'$gte': cutoff_time}
        }
        
        return list(self.collection.find(query).sort('timestamp', -1))
    
    def print_summary(self, hours: int = 24):
        """Print a summary of recent activity"""
        print(f"\n=== OpenVPN Connection Summary (Last {hours} hours) ===")
        
        summary = self.get_connection_summary(hours)
        
        if not summary:
            print("No connection events found in the specified time period.")
            return
        
        total_events = sum(event['count'] for event in summary.values())
        total_clients = len(set().union(*[event['unique_clients'] for event in summary.values() if event['unique_clients']]))
        
        print(f"Total Events: {total_events}")
        print(f"Unique Clients: {total_clients}")
        print("\nEvent Breakdown:")
        
        for event_type, data in summary.items():
            print(f"  {event_type}: {data['count']} events ({data['unique_clients']} unique clients)")
    
    def print_top_clients(self, hours: int = 24, limit: int = 10):
        """Print top clients by connection count"""
        print(f"\n=== Top Clients (Last {hours} hours) ===")
        
        clients = self.get_top_clients(hours, limit)
        
        if not clients:
            print("No client data found.")
            return
        
        print(f"{'IP Address':<15} {'Total':<6} {'Connects':<9} {'Disconnects':<12} {'Auth Failures':<13} {'Last Seen'}")
        print("-" * 80)
        
        for client in clients:
            ip = client['_id']
            total = client['total_connections']
            connects = client['connect_events']
            disconnects = client['disconnect_events']
            auth_failures = client['auth_failures']
            last_seen = client['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{ip:<15} {total:<6} {connects:<9} {disconnects:<12} {auth_failures:<13} {last_seen}")
    
    def print_timeline(self, hours: int = 24, limit: int = 20):
        """Print recent connection timeline"""
        print(f"\n=== Recent Connection Timeline (Last {hours} hours) ===")
        
        events = self.get_connection_timeline(hours)[:limit]
        
        if not events:
            print("No recent events found.")
            return
        
        print(f"{'Timestamp':<19} {'Event':<12} {'Client IP':<15} {'Virtual IP':<15} {'Server'}")
        print("-" * 80)
        
        for event in events:
            timestamp = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            event_type = event['event_type']
            client_ip = event['client_ip']
            virtual_ip = event.get('virtual_ip', '')
            server = event.get('server_name', '')
            
            print(f"{timestamp:<19} {event_type:<12} {client_ip:<15} {virtual_ip:<15} {server}")
    
    def print_hourly_stats(self, hours: int = 24):
        """Print hourly statistics"""
        print(f"\n=== Hourly Statistics (Last {hours} hours) ===")
        
        stats = self.get_hourly_stats(hours)
        
        if not stats:
            print("No hourly statistics found.")
            return
        
        print(f"{'Date/Time':<16} {'Total':<6} {'Connects':<9} {'Disconnects':<12} {'Auth Failures'}")
        print("-" * 60)
        
        for stat in stats:
            date_id = stat['_id']
            date_str = f"{date_id['year']}-{date_id['month']:02d}-{date_id['day']:02d} {date_id['hour']:02d}:00"
            
            total = stat['total_events']
            connects = stat['connect_events']
            disconnects = stat['disconnect_events']
            auth_failures = stat['auth_failures']
            
            print(f"{date_str:<16} {total:<6} {connects:<9} {disconnects:<12} {auth_failures}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='OpenVPN Logger Data Analyzer')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    parser.add_argument('--client', type=str, help='Search for specific client IP')
    parser.add_argument('--summary', action='store_true', help='Show connection summary')
    parser.add_argument('--top-clients', action='store_true', help='Show top clients')
    parser.add_argument('--timeline', action='store_true', help='Show recent timeline')
    parser.add_argument('--hourly', action='store_true', help='Show hourly statistics')
    parser.add_argument('--system', action='store_true', help='Show system statistics')
    
    args = parser.parse_args()
    
    analyzer = OpenVPNAnalyzer()
    
    if args.client:
        print(f"\n=== Events for Client {args.client} ===")
        events = analyzer.search_by_client_ip(args.client, args.hours)
        
        if not events:
            print(f"No events found for client {args.client}")
        else:
            print(f"{'Timestamp':<19} {'Event':<12} {'Virtual IP':<15} {'Server'}")
            print("-" * 60)
            
            for event in events:
                timestamp = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                event_type = event['event_type']
                virtual_ip = event.get('virtual_ip', '')
                server = event.get('server_name', '')
                
                print(f"{timestamp:<19} {event_type:<12} {virtual_ip:<15} {server}")
    
    elif args.system:
        print(f"\n=== System Statistics (Last {args.hours} hours) ===")
        stats = analyzer.get_system_stats(args.hours)
        
        if not stats:
            print("No system statistics found.")
        else:
            print(f"{'Timestamp':<19} {'CPU %':<6} {'Memory %':<9} {'Disk %':<7}")
            print("-" * 50)
            
            for stat in stats[:20]:  # Show last 20 entries
                timestamp = stat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                cpu = stat['stats'].get('cpu_percent', 0)
                memory = stat['stats'].get('memory_percent', 0)
                disk = stat['stats'].get('disk_percent', 0)
                
                print(f"{timestamp:<19} {cpu:<6.1f} {memory:<9.1f} {disk:<7.1f}")
    
    else:
        # Default behavior - show summary
        analyzer.print_summary(args.hours)
        analyzer.print_top_clients(args.hours, 10)
        analyzer.print_timeline(args.hours, 20)


if __name__ == "__main__":
    main()
