'''
Author: SheathedSharp429 z404878860@163.com
Date: 2024-09-08 17:34:56
'''
from PyQt5.QtCore import QThread, pyqtSignal
import scapy.all as scapy
from collections import deque
import time
import logging

class PacketCapture(QThread):
    packets_captured = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.interface = None
        self.is_running = False
        self.captured_packets = []
        self.packet_buffer = deque(maxlen=1000)  # 缓冲最多1000个数据包
        self.last_emit_time = 0
        self.capture_rate = 1000  # 每秒最多处理1000个数据包
        self.last_capture_time = 0

    def set_interface(self, interface):
        self.interface = interface

    def run(self):
        self.is_running = True
        self.captured_packets.clear()
        try:
            scapy.sniff(iface=self.interface, prn=self.process_packet, store=False, 
                        stop_filter=lambda _: not self.is_running)
        except Exception as e:
            self.error_occurred.emit(f"Packet capture error: {str(e)}")
            logging.error(f"Packet capture error: {str(e)}")

    def process_packet(self, packet):
        current_time = time.time()
        if current_time - self.last_capture_time < 1 / self.capture_rate:
            return  # 限制捕获速率

        self.last_capture_time = current_time
        self.packet_buffer.append(packet)
        self.captured_packets.append(packet)  # 添加这一行以存储捕获的数据包
        
        if current_time - self.last_emit_time > 0.5:  # 每0.5秒发送一次数据
            packets_to_emit = list(self.packet_buffer)
            self.packets_captured.emit(packets_to_emit)
            self.packet_buffer.clear()
            self.last_emit_time = current_time

    def stop(self):
        self.is_running = False

    def get_packet(self, index):
        if 0 <= index < len(self.captured_packets):
            return self.captured_packets[index]
        return None

    def get_all_packets(self):
        return self.captured_packets

    def save_packets(self, file_path):
        scapy.wrpcap(file_path, self.captured_packets)

    @staticmethod
    def get_available_interfaces():
        return scapy.get_if_list()