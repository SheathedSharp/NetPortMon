'''
Author: SheathedSharp z404878860@163.com
Date: 2024-09-08 17:29:59
'''
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.main_window import MainWindow
from core.packet_capture import PacketCapture
from core.packet_analyzer import PacketAnalyzer

class NetworkMonitor:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.packet_capture = PacketCapture()
        self.packet_analyzer = PacketAnalyzer()

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    monitor = NetworkMonitor()
    monitor.run()

