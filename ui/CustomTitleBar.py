import sys

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from ui.titleBarQT import Ui_titleBar

class MyBar(Ui_titleBar):

    def __init__(self, parent):
        super(MyBar, self).__init__()
        self.setupUi(self)
        self.parent = parent

        self.btn_close.clicked.connect(self.btn_close_clicked)


        self.btn_min.clicked.connect(self.btn_min_clicked)

        self.start = QPoint(0, 0)
        self.pressing = False
        self.dpos = 0

    def resizeEvent(self, QResizeEvent):
        super(MyBar, self).resizeEvent(QResizeEvent)
        self.title.setFixedWidth(self.parent.width())

    def mousePressEvent(self, event):
        self.dpos = self.mapToGlobal(event.pos()) - QPoint(self.parent.geometry().x(), self.parent.geometry().y())
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            self.parent.move(self.mapToGlobal(event.pos()) - self.dpos)


    def mouseReleaseEvent(self, QMouseEvent):
        self.pressing = False

    def btn_close_clicked(self):
        self.parent.close()

    def btn_max_clicked(self):
        self.parent.showMaximized()

    def btn_min_clicked(self):
        self.parent.showMinimized()