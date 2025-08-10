import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathlib import Path
import threading

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, Qt, QRegExp, QTimer, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QRegExpValidator, QPainter, QColor
from PyQt5.QtWidgets import QLabel, QGraphicsColorizeEffect, QApplication, QPushButton, QDialog

from ui import frameSettings, mainWindow, CustomTitleBar, CollapsibleBox
from ui.SideGrip import SideGrip
import nickAnswer

from videoProcessing import GenshinVoicer
import json
import multiprocessing
import re
import ctypes, os
import math

import ctypes
import keyboard
import soundfile as sf
import sounddevice as sd

root = os.path.dirname(__file__) + "/../"

myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

settings = dict()

regex = "[0-9]"
pattern = re.compile(regex)

def isAdmin():
    try:
        is_admin = (os.getuid() == 0)
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin


class WindowApp(QtWidgets.QMainWindow, mainWindow.Ui_MainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__()

        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        app_icon = QtGui.QIcon()
        app_icon.addFile(root + 'data/Logos/Logo16x16.png', QtCore.QSize(16, 16))
        app_icon.addFile(root +'data/Logos/Logo24x24.png', QtCore.QSize(24, 24))
        app_icon.addFile(root +'data/Logos/Logo32x32.png', QtCore.QSize(32, 32))
        app_icon.addFile(root +'data/Logos/Logo48x48.png', QtCore.QSize(48, 48))
        app_icon.addFile(root +'data/Logos/Logo256x256.png', QtCore.QSize(256, 256))
        app_icon.addFile(root +'data/Logos/Logo512x512.png', QtCore.QSize(512, 512))
        self.setWindowIcon(app_icon)

        self.frameSettingsForm = frameSettings.Ui_Form()
        self.frameSettingsForm.setupUi(self)
        self.settingCollapsedBox = CollapsibleBox.CollapsibleBox("Настройки")
        lay = QtWidgets.QVBoxLayout(self.settingCollapsedBox)
        lay.setAlignment(Qt.AlignTop)
        lay.addWidget(self.frameSettingsForm.frameSettings)
        self.settingCollapsedBox.setContentLayout(lay)
        self.settingCollapsedBox.addAnim(self)
        self.verticalLayoutSettingsBase.setAlignment(Qt.AlignTop)
        self.verticalLayoutSettingsBase.addWidget(self.settingCollapsedBox)

        customTitleBar = CustomTitleBar.MyBar(self)
        self.verticalLayoutTitle.addWidget(customTitleBar)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(430, 200)
        self.setWindowTitle("Genshin Speaker")

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

        # Конец добавления элементов Qt

        reg_ex = QRegExp("[а-яёА-ЯЁ ]+")
        input_validator = QRegExpValidator(reg_ex, self.frameSettingsForm.VoicePlayerNameLineEdit)
        self.frameSettingsForm.VoicePlayerNameLineEdit.setValidator(input_validator)

        self.jsonFileName = root + 'data/settings.json'
        global settings
        if not Path(self.jsonFileName).is_file():
            settings = {"proc": "cuda", "monitor": "Display 1", "speachSpeed": 1.0, "volume": 50, "autoSwitchDial": False, "detectPlayerName": True,
             "playerName": "", "playerVoiceName": "", "travelerGenderIsMale": True, "muteNoEventNpc": True}
            with open(self.jsonFileName, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False)
        else:
            with open(self.jsonFileName, 'r', encoding='utf-8') as openfile:
                settings = json.load(openfile)


        self.genshinVoicer = GenshinVoicer()

        if settings.get("proc"):
            if settings.get("proc") == 'cuda' and self.genshinVoicer.isCudaAvailable():
                self.frameSettingsForm.GPU_rBtn.setChecked(True)
                self.frameSettingsForm.CPU_rBtn.setChecked(False)
                self.genshinVoicer.proc = 'cuda'
            else:
                self.frameSettingsForm.GPU_rBtn.setChecked(False)
                self.frameSettingsForm.CPU_rBtn.setChecked(True)
                self.genshinVoicer.proc = 'cpu'
        else:
            if self.genshinVoicer.isCudaAvailable():
                self.frameSettingsForm.GPU_rBtn.setChecked(True)
                self.frameSettingsForm.CPU_rBtn.setChecked(False)
                self.genshinVoicer.proc = 'cuda'
            else:
                self.frameSettingsForm.GPU_rBtn.setChecked(False)
                self.frameSettingsForm.CPU_rBtn.setChecked(True)
                self.genshinVoicer.proc = 'cpu'
            settings["proc"] = self.genshinVoicer.proc
            with open(self.jsonFileName, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False)

        self.genshinVoicer.cudaAvailable.connect(self.changeCudaShow)
        self.changeCudaShow(self.genshinVoicer.isCudaAvailable())

        if isAdmin():
            self.frameSettingsForm.switchDialCheckBox.setEnabled(True)
            self.frameSettingsForm.switchDialCheckBox.setText("Автоматически переключать диалоги\n(Является сторонним вмешательством в игровой процесс)")
            if settings.get("autoSwitchDial") is not None:
                if settings.get("autoSwitchDial"):
                    self.frameSettingsForm.switchDialCheckBox.setChecked(True)
                    self.genshinVoicer.switchDial = True
            else:
                self.frameSettingsForm.switchDialCheckBox.setChecked(False)
                self.genshinVoicer.switchDial = False

            self.frameSettingsForm.switchDialCheckBox.keyPressEvent = self.ignore_key_press
            self.frameSettingsForm.switchDialCheckBox.stateChanged.connect(self.changeSwitchDial)
        else:
            self.frameSettingsForm.switchDialCheckBox.setText("Автоматически переключать диалоги \n"
"(Перезапустите приложение от имени Администратора)")
            self.genshinVoicer.switchDial = False
            self.frameSettingsForm.switchDialCheckBox.setChecked(False)
            self.frameSettingsForm.switchDialCheckBox.setEnabled(False)

        if settings.get("muteNoEventNpc") is not None:
            self.frameSettingsForm.muteNoEventNpcCheckBox.setChecked(settings.get("muteNoEventNpc"))
        self.genshinVoicer.setMuteStateForCertainCharacters(self.frameSettingsForm.muteNoEventNpcCheckBox.isChecked())

        self.frameSettingsForm.showMonitorNumbers.clicked.connect(self.ShowMonitorNumbers)
        self.startStopVoicerBtn.hide()
        self.frameSettingsForm.label_2.hide()

        self.app = QApplication.instance()
        self.screens_available = self.app.screens()

        for screen in self.screens_available:
            self.frameSettingsForm.choiceMonitorCB.addItem("Display " + pattern.search(screen.name()).group(0))
        if len(self.screens_available) == 1:
            self.frameSettingsForm.choiceMonitorCB.setCurrentIndex(0)
            self.frameSettingsForm.groupBoxMonitors.hide()
        else:
            self.frameSettingsForm.choiceMonitorCB.addItem("Монитор не выбран")
            self.frameSettingsForm.choiceMonitorCB.setCurrentIndex(self.frameSettingsForm.choiceMonitorCB.count() - 1)
        if settings.get("monitor"):
            self.frameSettingsForm.choiceMonitorCB.setCurrentText(settings.get("monitor"))
        self.setMonitor()


        if settings.get("volume"):
            self.frameSettingsForm.volSlider.setValue(settings.get("volume"))

        self.frameSettingsForm.minVolLabel.setText(str(self.frameSettingsForm.volSlider.minimum()))
        self.frameSettingsForm.maxVolLabel.setText(str(self.frameSettingsForm.volSlider.maximum()))
        self.frameSettingsForm.volLabel.setText(str(self.frameSettingsForm.volSlider.value()))


        self.frameSettingsForm.volSlider.valueChanged.connect(self.volChanged)

        if settings.get("detectPlayerName") is not None:
            self.frameSettingsForm.groupBoxPlayerNicks.setChecked(bool(settings.get("detectPlayerName")))

        self.genshinVoicer.detectPlayerName = self.frameSettingsForm.groupBoxPlayerNicks.isChecked()

        self.frameSettingsForm.PlayerNameLineEdit.textChanged.connect(self.PlayerNameLineEditChanged)
        self.frameSettingsForm.VoicePlayerNameLineEdit.textChanged.connect(self.VoicePlayerNameLineEditChanged)
        if settings.get("playerName") and settings.get("playerVoiceName"):
            self.frameSettingsForm.PlayerNameLineEdit.setText(settings.get("playerName"))
            self.frameSettingsForm.VoicePlayerNameLineEdit.setText(settings.get("playerVoiceName"))
        else:
            self.frameSettingsForm.PlayerNameLineEdit.setText("Nickname")
            self.frameSettingsForm.VoicePlayerNameLineEdit.setText("Никнэйм")
            if self.frameSettingsForm.groupBoxPlayerNicks.isChecked():
                self.start_animation_blink_alert()

        self.frameSettingsForm.maleTrevelerGb.toggled.connect(self.changedTravelerGenderAsMale)
        self.frameSettingsForm.femaleTrevelerGb.toggled.connect(self.changedTravelerGenderAsFemale)
        if settings.get("travelerGenderIsMale") is not None:
            if settings["travelerGenderIsMale"]:
                self.frameSettingsForm.maleTrevelerGb.setChecked(True)
            else:
                self.frameSettingsForm.femaleTrevelerGb.setChecked(True)

        self.frameSettingsForm.CPU_rBtn.toggled.connect(lambda : self.changeProc('cpu'))
        self.frameSettingsForm.GPU_rBtn.toggled.connect(lambda: self.changeProc('cuda'))

        self.frameSettingsForm.choiceMonitorCB.currentTextChanged.connect(self.setMonitor)

        self.frameSettingsForm.saveSettingsBtn.clicked.connect(self.saveSettings)

        self.startStopVoicerBtn.clicked.connect(self.StartStopSpeak)

        self.frameSettingsForm.speachSpeedSpinBox.valueChanged.connect(self.speachSpeedChanged)

        self.frameSettingsForm.showCV_chBtn.stateChanged.connect(self.showHideCV)

        self.frameSettingsForm.nickQuestionBtn.clicked.connect(self.showNickAnswer)

        self.frameSettingsForm.groupBoxPlayerNicks.toggled.connect(self.changePlayerNickState)

        self.frameSettingsForm.muteNoEventNpcCheckBox.stateChanged.connect(self.changeMuteNoEventNPC)


        self.runLongTask()

        self.pausePixMap = QtGui.QPixmap(root +"data/Logos/iconPause.png")
        self.playPixMap = QtGui.QPixmap(root +"data/Logos/iconPlay.png")
        self.playSound = sf.read(root +"data/Sound/playSound.mp3")
        self.pauseSound = sf.read(root +"data/Sound/pauseSound.mp3")


        print("Работа запущена")


    def changedTravelerGenderAsMale(self):
        if self.frameSettingsForm.maleTrevelerGb.isChecked():
            self.genshinVoicer.setTravelerGender(True)

    def changedTravelerGenderAsFemale(self):
        if self.frameSettingsForm.femaleTrevelerGb.isChecked():
            self.genshinVoicer.setTravelerGender(False)

    def changeMuteNoEventNPC(self):
        self.genshinVoicer.setMuteStateForCertainCharacters(self.frameSettingsForm.muteNoEventNpcCheckBox.isChecked())

    def changePlayerNickState(self):
        if self.genshinVoicer:
            self.genshinVoicer.detectPlayerName = self.frameSettingsForm.groupBoxPlayerNicks.isChecked()
        if self.frameSettingsForm.groupBoxPlayerNicks.isChecked() \
            and self.frameSettingsForm.PlayerNameLineEdit.text() == "Nickname":
            self.start_animation_blink_alert()
        else:
            self.stop_animation_blink_alert()
        print(15)

    def showNickAnswer(self):
        winAns = nickAnswer.WindowApp()
        winAns.show()

    def showEvent(self, event):
        if hasattr(self, "alertLabel1"):
            pos = self.settingCollapsedBox.toggle_button.mapTo(self, self.settingCollapsedBox.toggle_button.pos())
            self.alertLabel1.move(pos.x() + self.settingCollapsedBox.toggle_button.width() + 5, pos.y() + 11)

    def updateBlinkAlert(self, alertTransperent:float = None):
        def getCss(transperent):
            css = \
            ("QFrame {\n"
            "    background-color: none;\n"
            "}\n"
            "\n"
            "#framePlayerNicks{\n"
             f"    border: 3px solid rgba(255,50,50, {transperent});\n"
            "    border-radius: 10px;  \n"
            "    background-color: rgba(255,255,255, 50);\n"
            "}\n"
            "\n"
            "#groupBoxPlayerNicks, #groupBoxTrevelerGender{\n"
            "    border-radius: 10px;  \n"
            "    background-color: rgba(255,255,255, 0);\n"
            "}\n"
            "\n"
            "QRadioButton {\n"
            "    background-color: rgba(255,255,255, 0);\n"
            "}\n"
            "QLineEdit{\n"
            "    border: 1px solid rgba(255,255,255, 40);\n"
            "    border-radius: 8px;  \n"
            "    background-color: rgba(255,255,255, 40);\n"
            "    padding-left: 5px;\n"
            "}\n"
            "QLineEdit::hover{\n"
            "    border-color:  rgba(255,255,255, 150);\n"
            "}\n"
            "QLineEdit:disabled, QLabel:disabled{\n"
            "    color:  rgba(255,255,255, 180);\n"
            "}")
            return css
        if alertTransperent is None:
            self.lastBorderI = self.lastBorderI + 2 * math.pi/20
            if self.lastBorderI > 2 * math.pi:
                self.lastBorderI = 0.0
            alertTransperent = 0.5 * (-math.cos(self.lastBorderI) + 1)

        self.frameSettingsForm.framePlayerNicks.setStyleSheet(getCss(alertTransperent))
        opacity = QtWidgets.QGraphicsOpacityEffect(self.alertLabel1)
        opacity.setOpacity(alertTransperent)
        self.alertLabel1.setGraphicsEffect(opacity)

    def stop_animation_blink_alert(self):
        if hasattr(self, "blinkAlertTimer"):
            self.blinkAlertTimer.stop()
            self.updateBlinkAlert(0.0)

    def start_animation_blink_alert(self):
        pixmap = QPixmap(root +'data/Logos/alert.png')
        self.alertLabel1 = QLabel(self)
        self.alertLabel1.setPixmap(pixmap)
        self.alertLabel1.setScaledContents(True)
        self.alertLabel1.setGeometry(0, 0, 15, 15)
        self.alertLabel1.setParent(self)
        self.alertLabel1.show()
        pos = self.settingCollapsedBox.toggle_button.mapTo(self, self.settingCollapsedBox.toggle_button.pos())
        self.alertLabel1.move(pos.x() + self.settingCollapsedBox.toggle_button.width() - 5, pos.y() + 3)
        self.updateBlinkAlert(0.0)

        self.blinkAlertTimer = QTimer(self)
        self.blinkAlertTimer.timeout.connect(self.updateBlinkAlert)
        self.blinkAlertTimer.start(60)
        self.lastBorderI = 0.0

    def PlayerNameLineEditChanged(self, val):
        self.genshinVoicer.playerName = val
        self.genshinVoicer.updatePlayerNickImg()

    def VoicePlayerNameLineEditChanged(self, val:str):
        if len(val) > 0:
            self.genshinVoicer.voicePlayerName = self.RemoveExtraSpacesInVocePlayerName(val)

    def RemoveExtraSpacesInVocePlayerName(self, val):
        while "  " in val:
            val = val.replace("  ", " ")
        if len(val) > 0:
            if val[0] == " ": val = val[1:]
        if len(val) > 1:
            if val[-1] == " ": val = val[:-2]
        return val

    def changeCudaShow(self, val):
        if not val:
            self.frameSettingsForm.groupBoxProcessers.hide()
            self.genshinVoicer.proc = 'cpu'
            self.frameSettingsForm.CPU_rBtn.setChecked(True)

    def ignore_key_press(self, event):
        pass

    def changeSwitchDial(self):
        self.genshinVoicer.switchDial = self.frameSettingsForm.switchDialCheckBox.isChecked()

    def showHideCV(self):
        if self.frameSettingsForm.showCV_chBtn.isChecked():
            self.genshinVoicer.showCVWindows()
        else:
            self.genshinVoicer.hideCVWindows()

    def volChanged(self, value):
        self.frameSettingsForm.volLabel.setText(str(value))
        self.genshinVoicer.setVolume(float(value)/100.0)


    def speachSpeedChanged(self, value):
        self.genshinVoicer.setSpeechSpeed(value)

    def StartStopSpeak(self):
        self.genshinVoicer.canSpeak = not self.genshinVoicer.canSpeak
        icon1 = QtGui.QIcon()
        if self.genshinVoicer.canSpeak:
            self.startStopVoicerBtn.setText("Остановить озвучку")
            icon1.addPixmap(self.pausePixMap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.startStopVoicerBtn.setIcon(icon1)
            sd.play(self.playSound[0] * float(self.frameSettingsForm.volSlider.value()) / 100.0, self.playSound[1])
        else:
            self.startStopVoicerBtn.setText("Возобновить озвучку")
            icon1.addPixmap(self.playPixMap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.startStopVoicerBtn.setIcon(icon1)
            sd.play(self.pauseSound[0] * float(self.frameSettingsForm.volSlider.value()) / 100.0, self.pauseSound[1])

    def saveSettings(self):
        #settings = {}
        settings["proc"] = self.genshinVoicer.proc
        if pattern.search(self.frameSettingsForm.choiceMonitorCB.currentText()):
            settings["monitor"] = self.frameSettingsForm.choiceMonitorCB.currentText()
        settings["speachSpeed"] = self.frameSettingsForm.speachSpeedSpinBox.value()
        settings["volume"] = self.frameSettingsForm.volSlider.value()
        settings["autoSwitchDial"] = self.frameSettingsForm.switchDialCheckBox.isChecked()
        settings["detectPlayerName"] = self.frameSettingsForm.groupBoxPlayerNicks.isChecked()
        if len(self.frameSettingsForm.PlayerNameLineEdit.text()) > 0 \
                and len(self.frameSettingsForm.VoicePlayerNameLineEdit.text()) > 0 \
                and self.frameSettingsForm.PlayerNameLineEdit.text() != "Nickname":
            settings["playerName"] = self.frameSettingsForm.PlayerNameLineEdit.text()
            settings["playerVoiceName"] = self.RemoveExtraSpacesInVocePlayerName(self.frameSettingsForm.VoicePlayerNameLineEdit.text())
            self.stop_animation_blink_alert()

        settings["travelerGenderIsMale"] = self.frameSettingsForm.maleTrevelerGb.isChecked()

        settings["muteNoEventNpc"] = self.frameSettingsForm.muteNoEventNpcCheckBox.isChecked()
        with open(self.jsonFileName, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False)

        self.timerSaveBtn = QTimer(self)
        self.timerSaveBtn.singleShot(150, self.setSaveBtnSavedView)  # for one time call only


    def setSaveBtnSavedView(self):
        self.frameSettingsForm.saveSettingsBtn.setText("Настройки сохранены")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(root +"data/Logos/iconSuccess.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.frameSettingsForm.saveSettingsBtn.setIcon(icon)

        self.timerSaveBtn.singleShot(3000, self.returnDefaultSaveBtnView)  # for one time call only


    def returnDefaultSaveBtnView(self):
        self.frameSettingsForm.saveSettingsBtn.setText("Сохранить настройки")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(root + "data/Logos/diskette.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.frameSettingsForm.saveSettingsBtn.setIcon(icon)

    def setMonitor(self):
        if pattern.search(self.frameSettingsForm.choiceMonitorCB.currentText()):
            mon = int(pattern.search(self.frameSettingsForm.choiceMonitorCB.currentText()).group(0))
            self.genshinVoicer.monitor = mon

    def changeProc(self, proc):
        self.genshinVoicer.proc = proc
        self.frameSettingsForm.label_2.show()

    def ShowMonitorNumbers(self):

        self.widgets = []
        i = 1
        for screen in self.screens_available:
            self.screen = screen

            app_widget = QLabel()
            app_widget.setPixmap(QPixmap(root +'data/Logos/blackBack.png'))
            app_widget.setAlignment(QtCore.Qt.AlignCenter)
            app_widget.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            app_widget.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            app_widget.setStyleSheet("background:transparent;")


            app_widget2 = QLabel(pattern.search(screen.name()).group(0))
            app_widget2.setAlignment(QtCore.Qt.AlignCenter)
            color_effect = QGraphicsColorizeEffect()
            color_effect.setColor(Qt.white)
            app_widget2.setGraphicsEffect(color_effect)
            font = app_widget2.font()
            font.setPointSize(100)
            app_widget2.setFont(font)
            app_widget2.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            app_widget2.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            app_widget2.setStyleSheet("background:transparent;")

            app_widget.show()
            app_widget.windowHandle().setScreen(self.screen)
            app_widget.showFullScreen()

            app_widget2.show()
            app_widget2.windowHandle().setScreen(self.screen)
            app_widget2.showFullScreen()

            self.widgets.append(app_widget)
            self.widgets.append(app_widget2)
            i = i + 1
        threading.Timer(5, self.closeMonitorWindgets).start()

    def closeMonitorWindgets(self):
        for widget in self.widgets:
            widget.close()

    def runLongTask(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object

        # Step 4: Move worker to the thread
        self.genshinVoicer.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.genshinVoicer.run)
        self.genshinVoicer.finished.connect(self.finish)
        self.genshinVoicer.finished.connect(self.thread.quit)
        self.genshinVoicer.finished.connect(self.genshinVoicer.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.genshinVoicer.progress.connect(self.progressBarUpdate)
        self.genshinVoicer.ready.connect(self.showReady)
        self.genshinVoicer.allObjectsCreated.connect(self.setupGenshinVoicer)

        # Step 6: Start the thread
        self.thread.start()

    def setupGenshinVoicer(self):
        if settings.get("speachSpeed"):
            self.genshinVoicer.setSpeechSpeed(settings.get("speachSpeed"))
            self.frameSettingsForm.speachSpeedSpinBox.setValue(settings.get("speachSpeed"))
        self.genshinVoicer.setVolume(float(self.frameSettingsForm.volSlider.value()) / 100.0)

    def progressBarUpdate(self, val):
        print("progress" + str(val))
        self.progressBar.setValue(val)

    def showReady(self):
        self.progressBar.hide()
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("MainWindow", "Готово. Откройте окно с игрой"))
        self.startStopVoicerBtn.show()

    def closeEvent(self, event):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("MainWindow", "Завершене работы"))
        self.genshinVoicer.canRun = False
        event.ignore()

    def finish(self):
        self.close()
        sys.exit()



    @property
    def gripSize(self):
        return self._gripSize

    def setGripSize(self, size):
        if size == self._gripSize:
            return
        self._gripSize = max(2, size)
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.gripSize] * 4)

        outRect = self.rect()
        # an "inner" rect used for reference to set the geometries of size grips
        inRect = outRect.adjusted(self.gripSize, self.gripSize,
                                  -self.gripSize, -self.gripSize)

        # top left
        self.cornerGrips[0].setGeometry(
            QtCore.QRect(outRect.topLeft(), inRect.topLeft()))
        # top right
        self.cornerGrips[1].setGeometry(
            QtCore.QRect(outRect.topRight(), inRect.topRight()).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QtCore.QRect(inRect.bottomRight(), outRect.bottomRight()))
        # bottom left
        self.cornerGrips[3].setGeometry(
            QtCore.QRect(outRect.bottomLeft(), inRect.bottomLeft()).normalized())

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top(), self.gripSize, inRect.height())
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left(), 0, inRect.width(), self.gripSize)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(),
            inRect.top(), self.gripSize, inRect.height())
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.gripSize, inRect.top() + inRect.height(),
            inRect.width(), self.gripSize)

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.updateGrips()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 255, 1))  # Почти прозрачный фон. Полностю просрачный нельзя, иначе просто не применится
        painter.setPen(Qt.transparent)
        painter.drawRect(self.rect())

def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = WindowApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()