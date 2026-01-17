import subprocess
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QFile, QUrl
from PySide6.QtUiTools import QUiLoader
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtGui import QPixmap, QPainter


def playerctl(cmd):
    try:
        return subprocess.check_output(
            ["playerctl"] + cmd, stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        return ""


class MediaOverlay(QWidget):
    def __init__(self):
        super().__init__()


        loader = QUiLoader()
        ui_file = QFile("layout.ui")
        ui_file.open(QFile.ReadOnly)


        
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.ui.playPauseButton.clicked.connect(lambda: playerctl(["play-pause"]))
        self.ui.skipButton.clicked.connect(lambda: playerctl(["next"]))
        self.ui.prevButton.clicked.connect(lambda: playerctl(["previous"]))


        self.timer = QTimer(self.ui)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_metadata)
        self.timer.start()
        self.update_metadata()
    
    def update_metadata(self):
        self.ui.label.setText(playerctl(["metadata", "--format", "{{artist}} - {{title}}"]))

        

        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MediaOverlay()

    # Position bottom-right
    
    screen = app.primaryScreen().availableGeometry()
    w.ui.show()
    w.move(
        screen.width() - w.width() - 20,
        screen.height() - w.height() - 20
    )

    
    sys.exit(app.exec())
