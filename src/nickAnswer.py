import sys  # sys нужен для передачи argv в QApplication

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from ui import CustomTitleBar
from ui.SideGrip import SideGrip
from ui import nickAnswerWindow

class WindowApp(QtWidgets.QMainWindow, nickAnswerWindow.Ui_MainWindow):
    _instance = None

    _shown = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WindowApp, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:

            self._initialized = True
            # Это здесь нужно для доступа к переменным, методам
            # и т.д. в файле design.py
            super().__init__()

            self.setupUi(self)  # Это нужно для инициализации нашего дизайна
            app_icon = QtGui.QIcon()
            app_icon.addFile('Logos/Logo16x16.png', QtCore.QSize(16, 16))
            app_icon.addFile('Logos/Logo24x24.png', QtCore.QSize(24, 24))
            app_icon.addFile('Logos/Logo32x32.png', QtCore.QSize(32, 32))
            app_icon.addFile('Logos/Logo48x48.png', QtCore.QSize(48, 48))
            app_icon.addFile('Logos/Logo256x256.png', QtCore.QSize(256, 256))
            app_icon.addFile('Logos/Logo512x512.png', QtCore.QSize(512, 512))
            self.setWindowIcon(app_icon)

            self.customTitleBar = CustomTitleBar.MyBar(self)
            self.customTitleBar.title.setText("Ответ на вопрос")
            self.verticalLayoutTitle.addWidget(self.customTitleBar)

            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.resize(430, 350)
            self.setWindowTitle("Ответ на вопрос")

            self._gripSize = 8
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.sideGrips = [
                SideGrip(self, QtCore.Qt.LeftEdge),
                SideGrip(self, QtCore.Qt.TopEdge),
                SideGrip(self, QtCore.Qt.RightEdge),
                SideGrip(self, QtCore.Qt.BottomEdge),
            ]

            # corner grips should be "on top" of everything, otherwise the side grips
            # will take precedence on mouse events, so we are adding them *after*;
            # alternatively, widget.raise_() can be used
            self.cornerGrips = [QtWidgets.QSizeGrip(self) for i in range(4)]
            self.setStyleSheet("background:transparent;")

            self.closeBtn.clicked.connect(self.close)

    def show(self):
        if not self._shown:
            self._shown = True
            super().show()
        else:
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        self._shown = False
        self._initialized = False
        self._instance = None
        event.accept()



def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = WindowApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()