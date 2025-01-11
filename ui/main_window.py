'''
Author: SheathedSharp429 z404878860@163.com
Date: 2024-09-08 17:33:50
'''
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QToolBar, QAction, QComboBox, QLabel, QMessageBox, QFileDialog, QProgressDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QSettings
from .packet_list_widget import PacketListWidget
from .packet_detail_widget import PacketDetailWidget
from .traffic_monitor_dialog import TrafficMonitorDialog
from .settings_dialog import SettingsDialog
from .history_chart_dialog import HistoryChartDialog
from core.packet_capture import PacketCapture
from core.packet_analyzer import PacketAnalyzer
from core.database_manager import DatabaseManager
import scapy.all as scapy
import json
from cryptography.fernet import Fernet
import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Port Traffic Monitor")
        self.setGeometry(100, 100, 1200, 800)

        self.packet_capture = PacketCapture()
        self.packet_capture.error_occurred.connect(self.handle_capture_error)
        self.packet_analyzer = PacketAnalyzer()
        self.db_manager = DatabaseManager()
        self.traffic_monitor_dialog = None
        self.history_chart_dialog = None
        self.capture_session_id = None
        self.settings = QSettings("SheathedSharp429", "NetworkMonitor")
        self.fernet = Fernet(self.get_or_create_key())

        self.load_settings()
        self.init_ui()

        self.packet_buffer = []
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # 每秒更新一次UI

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.create_toolbar()

        interface_layout = QHBoxLayout()
        interface_label = QLabel("选择网络接口:")
        self.interface_combo = QComboBox()
        self.interface_combo.addItems(scapy.get_if_list())
        interface_layout.addWidget(interface_label)
        interface_layout.addWidget(self.interface_combo)

        main_layout.addLayout(interface_layout)

        packet_layout = QHBoxLayout()
        self.packet_list = PacketListWidget()
        self.packet_detail = PacketDetailWidget()
        packet_layout.addWidget(self.packet_list, 2)
        packet_layout.addWidget(self.packet_detail, 1)

        main_layout.addLayout(packet_layout)

        self.packet_list.packet_selected.connect(self.show_packet_details)

    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        start_action = QAction(QIcon("resources/icons/start.png"), "开始捕获", self)
        start_action.triggered.connect(self.start_capture)
        toolbar.addAction(start_action)

        stop_action = QAction(QIcon("resources/icons/stop.png"), "停止捕获", self)
        stop_action.triggered.connect(self.stop_capture)
        toolbar.addAction(stop_action)

        clear_action = QAction(QIcon("resources/icons/clear.png"), "清空数据包", self)
        clear_action.triggered.connect(self.clear_packets)
        toolbar.addAction(clear_action)

        save_action = QAction(QIcon("resources/icons/save.png"), "保存数据包", self)
        save_action.triggered.connect(self.save_packets)
        toolbar.addAction(save_action)

        settings_action = QAction(QIcon("resources/icons/settings.png"), "数据库设置", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)

        history_chart_action = QAction(QIcon("resources/icons/chart.png"), "历史流量图表", self)
        history_chart_action.triggered.connect(self.show_history_chart)
        toolbar.addAction(history_chart_action)

    def show_settings_dialog(self):
        current_settings = {
            'host': self.db_manager.host,
            'port': self.db_manager.port,
            'db': self.db_manager.db,
            'username': self.db_manager.username,
            'password': self.db_manager.password
        }
        dialog = SettingsDialog(current_settings, self)
        dialog.settings_updated.connect(self.update_database_settings)
        dialog.settings_cleared.connect(self.clear_settings)
        dialog.exec_()

    def clear_settings(self):
        self.settings.clear()
        self.db_manager.update_connection(None, None, None, None, None)
        self.capture_session_id = None
        QMessageBox.information(self, "设置已清空", "所有数据库设置已被清空")

    def update_database_settings(self, host, port, db, username, password):
        self.db_manager.update_connection(host, int(port), db, username, password)
        self.save_settings(host, port, db, username, password)

    def start_capture(self):
        selected_interface = self.interface_combo.currentText()
        if not selected_interface:
            QMessageBox.warning(self, "警告", "请选择一个网络接口")
            return

        self.packet_capture.set_interface(selected_interface)
        self.packet_capture.packets_captured.connect(self.process_captured_packets)
        self.packet_capture.start()

        if self.db_manager.is_connected():
            self.capture_session_id = self.db_manager.create_capture_session()
        else:
            self.capture_session_id = None

        # Create and show TrafficMonitorDialog
        if not self.traffic_monitor_dialog:
            self.traffic_monitor_dialog = TrafficMonitorDialog(self)
        self.traffic_monitor_dialog.show()

        self.disable_actions()

    def stop_capture(self):
        if self.packet_capture.is_running:
            self.packet_capture.stop()
            self.packet_capture.packets_captured.disconnect(self.process_captured_packets)
            
            if self.db_manager.is_connected() and self.capture_session_id is not None:
                reply = QMessageBox.question(self, '确认', '是否将捕获的数据包同步数据库？',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.sync_to_database()
                else:
                    QMessageBox.information(self, "捕获完成", "数据包捕获已完成，但未同步到数据库。")
            else:
                QMessageBox.information(self, "捕获完成", "数据包捕获已完成。您可以使用保存功能将数据保存到文件。")

            # Hide the TrafficMonitorDialog
            if self.traffic_monitor_dialog:
                self.traffic_monitor_dialog.hide()

            self.enable_actions()

    @pyqtSlot(list)
    def process_captured_packets(self, packets):
        for packet in packets:
            try:
                summary, details = self.packet_analyzer.analyze_packet(packet)
                self.packet_buffer.append((summary, details))  # 存储摘要和详细信息
                
                if self.db_manager.is_connected() and self.capture_session_id is not None:
                    self.db_manager.insert_packet(self.capture_session_id, json.dumps(summary))
            except Exception as e:
                logging.error(f"Error processing packet: {str(e)}")

    def update_ui(self):
        if self.packet_buffer:
            packets_to_add = self.packet_buffer[:100]  # 每次最多添加100个数据包到UI
            for summary, details in packets_to_add:  # 解包摘要和详细息
                self.packet_list.add_packet(summary)
                if self.traffic_monitor_dialog:
                    self.traffic_monitor_dialog.update_traffic(summary)
                # 这里可以选择在添加到列表时更新详细信息
            self.packet_buffer = self.packet_buffer[100:]

    def sync_to_database(self):
        if self.capture_session_id is not None:
            packets = self.packet_capture.get_all_packets()
            total_packets = len(packets)

            # 估计总大小
            total_size = sum(len(json.dumps(self.packet_analyzer.analyze_packet(packet)[0])) for packet in packets)

            estimated_time = total_size / (1024 * 10)  # 假设上传速度为10KB/s
            show_progress = estimated_time > 1  # 如果预计时间大于1秒，则显示进度条

            if show_progress:
                progress = QProgressDialog("同步数据到数据库...", "取消", 0, total_packets, self)
                progress.setWindowModality(Qt.WindowModal)

            for i, packet in enumerate(packets):
                if show_progress and progress.wasCanceled():
                    break
                summary, _ = self.packet_analyzer.analyze_packet(packet)
                self.db_manager.insert_packet(self.capture_session_id, json.dumps(summary))  # 确保 summary 是可序列化的
                if show_progress:
                    progress.setValue(i + 1)

            if show_progress:
                progress.setValue(total_packets)  # 确保进度条达到最大值
                progress.close()  # 关闭进度条

            QMessageBox.information(self, "同步成功", "数据包已同步到数据库")

    def show_packet_details(self, row):
        packet = self.packet_capture.get_packet(row)  # 确保 row 是有效的索引
        if packet:
            _, details = self.packet_analyzer.analyze_packet(packet)
            self.packet_detail.set_details(details)
        else:
            self.packet_detail.set_details("未找到数据包")

    def clear_packets(self):
        self.packet_list.clear()
        self.packet_detail.clear()
        if self.traffic_monitor_dialog:
            self.traffic_monitor_dialog.clear()

    def save_packets(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存数据包", "", "PCAP Files (*.pcap);;All Files (*)")
        if file_path:
            self.packet_capture.save_packets(file_path)
            QMessageBox.information(self, "保存成功", f"数据包已保存到 {file_path}")

    def show_traffic_monitor(self):
        if not self.traffic_monitor_dialog:
            self.traffic_monitor_dialog = TrafficMonitorDialog(self)
        self.traffic_monitor_dialog.show()

    def show_history_chart(self):
        if not self.history_chart_dialog:
            self.history_chart_dialog = HistoryChartDialog(self.db_manager, self)
        self.history_chart_dialog.show()

    def disable_actions(self):
        for action in self.findChildren(QAction):
            if action.text() not in ["停止捕获", "清空数据包"]:
                action.setEnabled(False)

    def enable_actions(self):
        for action in self.findChildren(QAction):
            action.setEnabled(True)

    def get_or_create_key(self):
        key = self.settings.value("encryption_key")
        if not key:
            key = Fernet.generate_key()
            self.settings.setValue("encryption_key", key)
        return key

    def encrypt(self, data):
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, data):
        return self.fernet.decrypt(data.encode()).decode()

    def load_settings(self):
        host = self.settings.value("db_host")
        port = self.settings.value("db_port")
        db = self.settings.value("db_name")
        username = self.settings.value("db_username")
        password = self.settings.value("db_password")

        if all([host, port, db, username, password]):
            try:
                host = self.decrypt(host)
                port = int(self.decrypt(port))
                db = self.decrypt(db)
                username = self.decrypt(username)
                password = self.decrypt(password)
                self.db_manager.update_connection(host, port, db, username, password)
            except Exception as e:
                logging.error(f"Error loading settings: {str(e)}")

    def save_settings(self, host, port, db, username, password):
        self.settings.setValue("db_host", self.encrypt(host))
        self.settings.setValue("db_port", self.encrypt(str(port)))
        self.settings.setValue("db_name", self.encrypt(db))
        self.settings.setValue("db_username", self.encrypt(username))
        self.settings.setValue("db_password", self.encrypt(password))

    def handle_capture_error(self, error_message):
        QMessageBox.critical(self, "捕获错误", error_message)
        self.stop_capture()