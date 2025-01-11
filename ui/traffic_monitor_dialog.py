'''
Author: SheathedSharp z404878860@163.com
Date: 2024-09-09 00:15:19
'''
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter
from collections import defaultdict

class TrafficMonitorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("流量监控图表")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout(self)
        
        # 添加进程选择下拉框
        self.filter_layout = QHBoxLayout()
        self.process_combo = QComboBox()
        self.process_combo.addItem("All Processes")
        self.filter_layout.addWidget(self.process_combo)
        
        self.apply_filter_button = QPushButton("应用筛选")
        self.apply_filter_button.clicked.connect(self.apply_filter)
        self.filter_layout.addWidget(self.apply_filter_button)
        
        self.layout.addLayout(self.filter_layout)

        self.chart = QChart()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.layout.addWidget(self.chart_view)

        self.series = {}
        self.traffic_data = defaultdict(list)
        self.max_data_points = 100
        self.current_filter = "All Processes"

        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        self.axis_x.setRange(0, self.max_data_points)
        self.axis_y.setRange(0, 1000)

        self.axis_x.setTitleText("Time")
        self.axis_y.setTitleText("Bytes")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(1000)  # Update every second

    def update_traffic(self, packet_summary):
        process = packet_summary.get('process', 'Unknown')
        if process != 'N/A':
            length = packet_summary.get('length', 0)
            self.traffic_data[process].append(length)
            if len(self.traffic_data[process]) > self.max_data_points:
                self.traffic_data[process] = self.traffic_data[process][-self.max_data_points:]
            
            # 检查进程是否已在下拉列表中，如果不在则添加
            if process not in [self.process_combo.itemText(i) for i in range(self.process_combo.count())]:
                self.process_combo.addItem(process)

    def update_chart(self):
        try:
            for series in self.series.values():
                self.chart.removeSeries(series)
            self.series.clear()

            for process, data in self.traffic_data.items():
                if self.current_filter == "All Processes" or process == self.current_filter:
                    series = QLineSeries()
                    series.setName(process)
                    
                    for i, value in enumerate(data):
                        series.append(i, value)
                    
                    self.chart.addSeries(series)
                    series.attachAxis(self.axis_x)
                    series.attachAxis(self.axis_y)
                    self.series[process] = series

            if self.traffic_data:
                max_value = max(max(data) for data in self.traffic_data.values())
                self.axis_y.setRange(0, max_value + 100)
            else:
                self.axis_y.setRange(0, 1000)
        except RuntimeError as e:
            print(f"Error updating chart: {e}")

    def clear(self):
        self.traffic_data.clear()
        for series in self.series.values():
            self.chart.removeSeries(series)
        self.series.clear()
        self.process_combo.clear()
        self.process_combo.addItem("All Processes")

    def apply_filter(self):
        self.current_filter = self.process_combo.currentText()
        self.update_chart()

    def hideEvent(self, event):
        # Override hideEvent to prevent the dialog from being destroyed when closed
        event.ignore()

    def closeEvent(self, event):
        # Override closeEvent to hide the dialog instead of closing it
        event.ignore()
        self.hide()
