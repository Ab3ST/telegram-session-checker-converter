import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from src.ui.main_window import MainWindow


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.getLogger('telethon').setLevel(logging.CRITICAL)
    logging.getLogger('pyrogram').setLevel(logging.CRITICAL)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseStyleSheetPropagationInWidgetStyles, True)
    
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor('#4a4a4a'))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor('#ffffff'))
    app.setPalette(palette)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
