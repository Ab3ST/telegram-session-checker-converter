from PyQt6.QtWidgets import QDialog, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from src.utils.theme import Theme


class BaseDialog(QDialog):
    def __init__(self, parent=None, colors=None):
        super().__init__(parent)
        self.colors = colors or Theme.LIGHT
        self.drag_position = None

    def setup_frameless(self, width: int, height: int):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(width, height)
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        shadow = QGraphicsDropShadowEffect()
        is_light = self.colors.get('main_bg') == '#f8f9fa'
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60 if is_light else 180))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        self.setStyleSheet(Theme.get_dialog_style(self.colors))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
