'''
Author: SheathedSharp429 z404878860@163.com
Date: 2024-09-08 17:34:25
'''
from PyQt5.QtWidgets import QTextEdit

class PacketDetailWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)

    def set_details(self, details):
        self.setText(details)

    def clear(self):
        self.setText("")
