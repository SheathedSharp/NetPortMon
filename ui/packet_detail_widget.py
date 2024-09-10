'''
Author: hiddenSharp429 z404878860@163.com
Date: 2024-09-08 17:34:25
LastEditors: hiddenSharp429 z404878860@163.com
LastEditTime: 2024-09-08 18:38:59
FilePath: /Network_port traffic_monitoring_system/ui/packet_detail_weight.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
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
