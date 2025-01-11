'''
Author: SheathedSharp z404878860@163.com
Date: 2024-09-09 14:08:55
'''
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal
import pymysql

class SettingsDialog(QDialog):
    settings_updated = pyqtSignal(str, str, str, str, str)
    settings_cleared = pyqtSignal()

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据库设置")
        self.setGeometry(300, 300, 300, 250)  # Increased height to accommodate new button

        layout = QVBoxLayout()

        # 主机地址
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("主机地址:"))
        self.host_input = QLineEdit()
        self.host_input.setText(current_settings.get('host', ''))
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)

        # 端口
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("端口:"))
        self.port_input = QLineEdit()
        self.port_input.setText(str(current_settings.get('port', '')))
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)

        # 数据库名
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("数据库名:"))
        self.db_input = QLineEdit()
        self.db_input.setText(current_settings.get('db', ''))
        db_layout.addWidget(self.db_input)
        layout.addLayout(db_layout)

        # 用户名
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名:"))
        self.username_input = QLineEdit()
        self.username_input.setText(current_settings.get('username', ''))
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # 密码
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText(current_settings.get('password', ''))
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # 按钮
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)

        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # 添加清空信息按钮
        self.clear_button = QPushButton("清空信息")
        self.clear_button.clicked.connect(self.clear_settings)
        layout.addWidget(self.clear_button)

        self.setLayout(layout)

    def test_connection(self):
        host = self.host_input.text()
        port = int(self.port_input.text())
        db = self.db_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            conn = pymysql.connect(host=host, port=port, db=db, user=username, password=password)
            conn.close()
            QMessageBox.information(self, "连接成功", "成功连接到数据库!")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"无法连接到数据库: {str(e)}")

    def save_settings(self):
        host = self.host_input.text()
        port = self.port_input.text()
        db = self.db_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        self.settings_updated.emit(host, port, db, username, password)
        self.accept()

    def clear_settings(self):
        reply = QMessageBox.question(self, '确认', '确定要清空所有设置信息吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.host_input.clear()
            self.port_input.clear()
            self.db_input.clear()
            self.username_input.clear()
            self.password_input.clear()
            self.settings_cleared.emit()
            QMessageBox.information(self, "清空成功", "所有设置信息已清空")
