'''
Author: hiddenSharp429 z404878860@163.com
Date: 2024-09-09 16:37:05
LastEditors: hiddenSharp429 z404878860@163.com
LastEditTime: 2024-09-09 21:30:40
FilePath: /Network_port traffic_monitoring_system/ui/history_cart_dialog.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE%E5%8F%82
'''
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, QTimeEdit, QComboBox, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt, QDate, QTime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import mplcursors
import numpy as np
import matplotlib.patches as patches

class HistoryChartDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("历史流量图表")
        self.setGeometry(100, 100, 1000, 800)

        # 设置中文字体
        self.font = FontProperties(fname='/System/Library/Fonts/PingFang.ttc', size=10)
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['PingFang SC'] + plt.rcParams['font.sans-serif']

        layout = QVBoxLayout()

        # 控制面板
        control_layout = QHBoxLayout()
        
        # 开始日期和时间
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("开始时间:"))
        self.start_date = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_time = QTimeEdit(QTime(0, 0))
        start_layout.addWidget(self.start_date)
        start_layout.addWidget(self.start_time)
        control_layout.addLayout(start_layout)

        # 结束日期和时间
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("结束时间:"))
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_time = QTimeEdit(QTime(23, 59))
        end_layout.addWidget(self.end_date)
        end_layout.addWidget(self.end_time)
        control_layout.addLayout(end_layout)

        self.chart_type = QComboBox()
        self.chart_type.addItems(["条形图", "饼状图"])
        control_layout.addWidget(self.chart_type)
        
        update_button = QPushButton("更新图表")
        update_button.clicked.connect(self.update_chart)
        control_layout.addWidget(update_button)

        layout.addLayout(control_layout)

        # 图表
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # 添加数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['端口', '入站流量', '出站流量', '总流量', '占比', '相关进程', '用户'])
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.update_chart()

    def update_chart(self):
        start_datetime = datetime.combine(self.start_date.date().toPyDate(), self.start_time.time().toPyTime())
        end_datetime = datetime.combine(self.end_date.date().toPyDate(), self.end_time.time().toPyTime())
        
        chart_type = self.chart_type.currentText()

        data = self.db_manager.get_traffic_data(start_datetime, end_datetime)

        # 清除旧图表
        self.ax.clear()
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        if chart_type == "条形图":
            self.create_bar_chart(data)
        else:
            self.create_pie_chart(data)

        self.update_table(data)

    def create_bar_chart(self, data):
        ports = list(data.keys())
        in_traffic = [d['in'] for d in data.values()]
        out_traffic = [d['out'] for d in data.values()]
        
        x = range(len(ports))
        width = 0.35
        
        in_bars = self.ax.bar(x, in_traffic, width, label='入站流量')
        out_bars = self.ax.bar([i + width for i in x], out_traffic, width, label='出站流量')
        
        self.ax.set_xlabel('端口', fontproperties=self.font)
        self.ax.set_ylabel('流量 (字节)', fontproperties=self.font)
        self.ax.set_title('端口流量统计 (Top 10)', fontproperties=self.font)
        self.ax.set_xticks([i + width/2 for i in x])
        self.ax.set_xticklabels(ports)
        
        self.ax.legend(prop=self.font)
        self.figure.tight_layout()

        def format_tooltip(sel):
            bar = sel.artist
            x, _ = sel.target
            index = int(round(x)) if bar in in_bars else int(round(x - width))
            if index < 0 or index >= len(ports):
                return ""
            port = ports[index]
            if bar in in_bars:
                direction = "入站"
                traffic = in_traffic[index]
            else:
                direction = "出站"
                traffic = out_traffic[index]
            processes = ', '.join(data[port]['processes'][:2])
            users = ', '.join(data[port]['users'][:2])
            return f"端口: {port}\n{direction}流量: {traffic} 字节\n进程: {processes}\n用户: {users}"

        cursor = mplcursors.cursor(in_bars + out_bars, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(format_tooltip(sel)))
        cursor.connect("add", lambda sel: sel.annotation.set_fontproperties(self.font))
        cursor.connect("add", lambda sel: sel.annotation.get_bbox_patch().set_facecolor("white"))
        cursor.connect("add", lambda sel: sel.annotation.get_bbox_patch().set_alpha(0.9))

        for artist in cursor.artists:
            artist.set_gid(artist.get_gid())
        self.canvas.draw()

    def create_pie_chart(self, data):
        ports = list(data.keys())
        total_traffic = [d['total'] for d in data.values()]
        
        wedges, texts, autotexts = self.ax.pie(total_traffic, labels=ports, autopct='%1.1f%%', startangle=90)
        self.ax.axis('equal')
        self.ax.set_title('端口总流量占比 (Top 10)', fontproperties=self.font)
        
        # 隐藏默认的标签和百分比文本
        for text in texts + autotexts:
            text.set_visible(False)
        
        self.figure.tight_layout()

        # 添加自定义标签
        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = wedge.r * 0.8 * np.cos(np.radians(angle))
            y = wedge.r * 0.8 * np.sin(np.radians(angle))
            self.ax.text(x, y, ports[i], ha='center', va='center', fontproperties=self.font)

        # 创建一个注释对象，但先不显示
        annotation = self.ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                                      arrowprops=dict(arrowstyle="->"),
                                      fontproperties=self.font, visible=False)

        def hover(event):
            if event.inaxes == self.ax:
                for i, wedge in enumerate(wedges):
                    cont, _ = wedge.contains(event)
                    if cont:
                        port = ports[i]
                        traffic = total_traffic[i]
                        processes = ', '.join(data[port]['processes'][:2])
                        users = ', '.join(data[port]['users'][:2])
                        percentage = (traffic / sum(total_traffic)) * 100
                        annotation.set_text(f"端口: {port}\n总流量: {traffic} 字节\n占比: {percentage:.1f}%\n进程: {processes}\n用户: {users}")
                        annotation.xy = (event.xdata, event.ydata)
                        annotation.set_visible(True)
                        self.canvas.draw_idle()
                        return
                annotation.set_visible(False)
                self.canvas.draw_idle()

        self.canvas.mpl_connect('motion_notify_event', hover)
        self.canvas.draw()

    def update_table(self, data):
        self.table.setRowCount(len(data))
        total_traffic = sum(d['total'] for d in data.values())
        
        for row, (port, traffic) in enumerate(data.items()):
            self.table.setItem(row, 0, QTableWidgetItem(str(port)))
            self.table.setItem(row, 1, QTableWidgetItem(str(traffic['in'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(traffic['out'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(traffic['total'])))
            percentage = (traffic['total'] / total_traffic) * 100 if total_traffic > 0 else 0
            self.table.setItem(row, 4, QTableWidgetItem(f"{percentage:.2f}%"))
            self.table.setItem(row, 5, QTableWidgetItem(', '.join(traffic['processes'])))
            self.table.setItem(row, 6, QTableWidgetItem(', '.join(traffic['users'])))
        self.table.resizeColumnsToContents()
