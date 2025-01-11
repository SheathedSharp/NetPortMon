'''
Author: SheathedSharp z404878860@163.com
Date: 2024-09-08 17:35:11
'''
import scapy.all as scapy
from datetime import datetime
import pytz
import psutil
from cachetools import TTLCache
import time

class PacketAnalyzer:
    PROTOCOL_MAP = {
        1: "ICMP",
        2: "IGMP",
        6: "TCP",
        17: "UDP",
        41: "IPv6",
        89: "OSPF",
        132: "SCTP"
    }

    def __init__(self):
        self.process_cache = TTLCache(maxsize=1000, ttl=60)  # 缓存1000个项目，有效期60秒

    def analyze_packet(self, packet):
        summary = {}
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        summary['time'] = datetime.fromtimestamp(packet.time, beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

        if packet.haslayer(scapy.IP):
            summary['source_ip'] = packet[scapy.IP].src
            summary['destination_ip'] = packet[scapy.IP].dst
            protocol_num = packet[scapy.IP].proto
            summary['protocol'] = self.PROTOCOL_MAP.get(protocol_num, str(protocol_num))

        if packet.haslayer(scapy.TCP):
            summary['source_port'] = packet[scapy.TCP].sport
            summary['destination_port'] = packet[scapy.TCP].dport
        elif packet.haslayer(scapy.UDP):
            summary['source_port'] = packet[scapy.UDP].sport
            summary['destination_port'] = packet[scapy.UDP].dport

        summary['length'] = len(packet)

        # 尝试获取进程信息
        try:
            process = self.get_process_by_connection(summary['source_ip'], summary['source_port'],
                                                     summary['destination_ip'], summary['destination_port'])
            if process:
                summary['process'] = process.name()
                try:
                    summary['user'] = process.username()
                except:
                    summary['user'] = 'Unknown'
            else:
                summary['process'] = 'System'
                summary['user'] = 'System'
        except:
            summary['process'] = 'Unknown'
            summary['user'] = 'Unknown'

        details = self.get_packet_details(packet)
        return summary, details

    def get_process_by_connection(self, src_ip, src_port, dst_ip, dst_port):
        cache_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
        if cache_key in self.process_cache:
            return self.process_cache[cache_key]

        process = self._get_process_by_connection(src_ip, src_port, dst_ip, dst_port)
        self.process_cache[cache_key] = process
        return process

    def _get_process_by_connection(self, src_ip, src_port, dst_ip, dst_port):
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.ip == src_ip and conn.laddr.port == src_port:
                    return psutil.Process(conn.pid)
                if conn.raddr and conn.raddr.ip == dst_ip and conn.raddr.port == dst_port:
                    return psutil.Process(conn.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        return None

    def get_packet_summary(self, packet):
        summary = {}
        
        # 获取时间（北京时间）
        beijing_tz = pytz.timezone('Asia/Shanghai')
        summary['time'] = datetime.fromtimestamp(packet.time, beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

        if packet.haslayer(scapy.IP):
            summary['source'] = packet[scapy.IP].src
            summary['destination'] = packet[scapy.IP].dst
            protocol_num = packet[scapy.IP].proto
            summary['protocol'] = self.PROTOCOL_MAP.get(protocol_num, str(protocol_num))
        elif packet.haslayer(scapy.Ether):
            summary['source'] = packet[scapy.Ether].src
            summary['destination'] = packet[scapy.Ether].dst
            summary['protocol'] = 'Ethernet'

        summary['length'] = len(packet)

        process_info = self.get_process_info(packet)
        if process_info:
            summary['process'] = process_info['name']
            summary['user'] = process_info['username']
        else:
            summary['process'] = 'N/A'
            summary['user'] = 'N/A'

        return summary

    def get_packet_details(self, packet):
        details = []
        
        # 获取时间（北京时间）
        beijing_tz = pytz.timezone('Asia/Shanghai')
        packet_time = datetime.fromtimestamp(packet.time, beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        details.append(f"时间: {packet_time}")

        # Ethernet layer
        if packet.haslayer(scapy.Ether):
            details.append(f"Ethernet:")
            details.append(f"  Source MAC: {packet[scapy.Ether].src}")
            details.append(f"  Destination MAC: {packet[scapy.Ether].dst}")

        # IP layer
        if packet.haslayer(scapy.IP):
            details.append(f"IP:")
            details.append(f"  Source IP: {packet[scapy.IP].src}")
            details.append(f"  Destination IP: {packet[scapy.IP].dst}")
            protocol_num = packet[scapy.IP].proto
            protocol_name = self.PROTOCOL_MAP.get(protocol_num, str(protocol_num))
            details.append(f"  Protocol: {protocol_name} ({protocol_num})")

        # TCP/UDP layer
        if packet.haslayer(scapy.TCP):
            details.append(f"TCP:")
            details.append(f"  Source Port: {packet[scapy.TCP].sport}")
            details.append(f"  Destination Port: {packet[scapy.TCP].dport}")
            details.append(f"  Flags: {packet[scapy.TCP].flags}")
        elif packet.haslayer(scapy.UDP):
            details.append(f"UDP:")
            details.append(f"  Source Port: {packet[scapy.UDP].sport}")
            details.append(f"  Destination Port: {packet[scapy.UDP].dport}")

        # 获取进程信息
        process_info = self.get_process_info(packet)
        if process_info:
            details.append(f"Process Info:")
            details.append(f"  Process Name: {process_info['name']}")
            details.append(f"  PID: {process_info['pid']}")
            details.append(f"  User: {process_info['username']}")

        # 获取字节数
        details.append(f"Bytes:")
        details.append(f"  Total: {len(packet)}")

        return "\n".join(details)

    def get_process_info(self, packet):
        try:
            if packet.haslayer(scapy.IP) and (packet.haslayer(scapy.TCP) or packet.haslayer(scapy.UDP)):
                local_port = packet[scapy.TCP].sport if packet.haslayer(scapy.TCP) else packet[scapy.UDP].sport
                remote_port = packet[scapy.TCP].dport if packet.haslayer(scapy.TCP) else packet[scapy.UDP].dport
                for conn in psutil.net_connections():
                    if conn.laddr.port == local_port and (not conn.raddr or conn.raddr.port == remote_port):
                        process = psutil.Process(conn.pid)
                        return {
                            'name': process.name(),
                            'pid': process.pid,
                            'username': process.username()
                        }
        except:
            pass
        return None
