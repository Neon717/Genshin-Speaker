from PyQt5 import QtCore, QtGui, QtWidgets

class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.expanded = False
        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.setChecked(self.expanded)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )

        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.setMaximumHeight(19)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )


    def addAnim(self, animObj):
        self.toggle_animation2 = QtCore.QParallelAnimationGroup(self)

        self.initial_rect = animObj.geometry()

        self.final_rect = QtCore.QRect(
            self.initial_rect.x(),
            self.initial_rect.y(),
            self.initial_rect.width(),
            animObj.maximumHeight()
        )

        self.animObj = animObj
        self.toggle_animation2.addAnimation(
            QtCore.QPropertyAnimation(self.animObj, b"geometry")
        )


    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.expanded
        self.expanded = not self.expanded
        self.toggle_button.setChecked(self.expanded)
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation2.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

        self.initial_rect = QtCore.QRect(
            self.animObj.geometry().x(),
            self.animObj.geometry().y(),
            self.initial_rect.width(),
            self.animObj.minimumHeight()
        )
        self.final_rect = QtCore.QRect(
            self.animObj.geometry().x(),
            self.animObj.geometry().y(),
            self.final_rect.width(),
            self.animObj.maximumHeight()
        )

        for i in range(self.toggle_animation2.animationCount()):
            animation = self.toggle_animation2.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(self.initial_rect)
            animation.setEndValue(self.final_rect)

        self.toggle_animation2.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        content_height = 600
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)
