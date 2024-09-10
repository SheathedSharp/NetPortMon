'''
Author: hiddenSharp429 z404878860@163.com
Date: 2024-09-08 21:04:44
LastEditors: hiddenSharp429 z404878860@163.com
LastEditTime: 2024-09-09 20:40:38
FilePath: /Network_port traffic_monitoring_system/core/database_manager.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE%E5%8F%82
'''
import pymysql
from datetime import datetime
import json
from collections import defaultdict

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.host = None
        self.port = None
        self.db = None
        self.username = None
        self.password = None

    def is_connected(self):
        return self.connection is not None and self.connection.open

    def update_connection(self, host, port, db, username, password):
        self.host = host
        self.port = port
        self.db = db
        self.username = username
        self.password = password
        self.connect()

    def connect(self):
        if self.host and self.port and self.db and self.username and self.password:
            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    user=self.username,
                    password=self.password
                )
                self.create_tables()
            except Exception as e:
                print(f"Error connecting to database: {e}")

    def create_tables(self):
        with self.connection.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS capture_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    start_time DATETIME
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS packets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT,
                    data JSON,
                    FOREIGN KEY (session_id) REFERENCES capture_sessions(id)
                )
            ''')
        self.connection.commit()

    def create_capture_session(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO capture_sessions (start_time) VALUES (%s)",
                (datetime.now(),)
            )
        self.connection.commit()
        return cursor.lastrowid

    def insert_packet(self, session_id, packet_data):
        if not self.connection:
            return

        with self.connection.cursor() as cursor:
            sql = """
            INSERT INTO packets (session_id, data) 
            VALUES (%s, %s)
            """
            cursor.execute(sql, (session_id, packet_data))
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()

    def get_traffic_data(self, start_time, end_time):
        if not self.connection:
            return {}

        with self.connection.cursor() as cursor:
            sql = """
            SELECT data FROM packets
            JOIN capture_sessions ON packets.session_id = capture_sessions.id
            WHERE capture_sessions.start_time BETWEEN %s AND %s
            """
            cursor.execute(sql, (start_time, end_time))
            results = cursor.fetchall()

        traffic_data = defaultdict(lambda: {'in': 0, 'out': 0, 'total': 0, 'processes': set(), 'users': set()})
        for row in results:
            packet_data = json.loads(row[0])
            src_port = packet_data.get('source_port', 0)
            dst_port = packet_data.get('destination_port', 0)
            length = packet_data.get('length', 0)
            process = packet_data.get('process', 'Unknown')
            user = packet_data.get('user', 'Unknown')
            
            traffic_data[src_port]['out'] += length
            traffic_data[dst_port]['in'] += length
            traffic_data[src_port]['total'] += length
            traffic_data[dst_port]['total'] += length
            traffic_data[src_port]['processes'].add(process)
            traffic_data[dst_port]['processes'].add(process)
            traffic_data[src_port]['users'].add(user)
            traffic_data[dst_port]['users'].add(user)

        # Convert sets to lists for JSON serialization
        for port_data in traffic_data.values():
            port_data['processes'] = list(port_data['processes'])
            port_data['users'] = list(port_data['users'])

        # Sort by total traffic and get top 10
        sorted_data = dict(sorted(traffic_data.items(), key=lambda x: x[1]['total'], reverse=True)[:10])
        return sorted_data
