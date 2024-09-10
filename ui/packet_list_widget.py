'''
Author: hiddenSharp429 z404878860@163.com
Date: 2024-09-08 17:34:07
LastEditors: hiddenSharp429 z404878860@163.com
LastEditTime: 2024-09-09 17:51:02
FilePath: /Network_port traffic_monitoring_system/ui/packet_list_widget.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE%E8%AE%BE%E8%AE%A1
'''
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal

class PacketListWidget(QTableWidget):
    packet_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(8)  # 增加列数
        self.setHorizontalHeaderLabels([
            '时间', '源IP', '源端口', '目的IP', '目的端口', 
            '协议', '长度', '进程名称' 
        ])
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.itemSelectionChanged.connect(self.on_selection_changed)

    def add_packet(self, packet_info):
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(packet_info.get('time', '')))
        self.setItem(row, 1, QTableWidgetItem(packet_info.get('source_ip', '')))
        self.setItem(row, 2, QTableWidgetItem(str(packet_info.get('source_port', ''))))
        self.setItem(row, 3, QTableWidgetItem(packet_info.get('destination_ip', '')))
        self.setItem(row, 4, QTableWidgetItem(str(packet_info.get('destination_port', ''))))
        self.setItem(row, 5, QTableWidgetItem(packet_info.get('protocol', '')))
        self.setItem(row, 6, QTableWidgetItem(str(packet_info.get('length', ''))))
        self.setItem(row, 7, QTableWidgetItem(packet_info.get('process', '')))
        self.resizeColumnsToContents()

    def on_selection_changed(self):
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            self.packet_selected.emit(selected_rows[0].row())

    def clear(self):
        self.setRowCount(0)
