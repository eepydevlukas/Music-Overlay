import subprocess
import sys
from functools import cached_property

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGraphicsBlurEffect
)
from PySide6.QtCore import Qt, QTimer, QFile, QUrl, QByteArray, QObject, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtGui import QPixmap, QPainter, QImage


def playerctl(cmd):
    try:
        return subprocess.check_output(
            ["playerctl"] + cmd, stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        return ""



class ImageDownloader(QObject):
    finished = Signal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager.finished.connect(self.handle_finished)

    @cached_property
    def manager(self):
        return QNetworkAccessManager()

    def start_download(self, url):
        self.manager.get(QNetworkRequest(url))

    def handle_finished(self, reply):
        if reply.error() != QNetworkReply.NoError:
            print("error: ", reply.errorString())
            return
        image = QImage()
        image.loadFromData(reply.readAll())
        self.finished.emit(image)

class MediaOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # --- Background ---
        self.bg = QLabel(self)
        self.bg.setScaledContents(False)
        self.bg.lower()  # keep it behind everything

        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(15)

        # --- Load UI ---
        loader = QUiLoader()
        ui_file = QFile("layout.ui")
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        ui_file.close()
        self.ui.setParent(self)
        self.ui.raise_()

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
        # self.bg is NOT in the layout; it covers the whole widget via resizeEvent

        # --- Buttons ---
        self.ui.playPauseButton.clicked.connect(lambda: playerctl(["play-pause"]))
        self.ui.skipButton.clicked.connect(lambda: playerctl(["next"]))
        self.ui.prevButton.clicked.connect(lambda: playerctl(["previous"]))

        # --- Timer & downloader ---
        self.downloader = ImageDownloader()
        self.downloader.finished.connect(self.update_art)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_metadata)
        self.timer.start()

        self.update_metadata()

    def resizeEvent(self, event):
        # Make background cover entire window
        self.bg.setGeometry(self.rect())
        if self.bg.pixmap():
            self.bg.setPixmap(
                self.bg.pixmap().scaled(
                    self.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
            )
        super().resizeEvent(event)
    
    def update_metadata(self):
        data = playerctl(["metadata", "--format", "{{artist}} - {{title}}"])

        if self.ui.label.text() != data:
            self.ui.label.setText(data)

            art_url = playerctl(["metadata", "mpris:artUrl"])
            if art_url:
                self.downloader.start_download(QUrl(art_url))

    def update_art(self, image):
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.bg.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        self.bg.setPixmap(scaled)
        self.bg.setGraphicsEffect(self.blur_effect)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MediaOverlay()
    
    w.resize(600, 200)  # initial size
    w.show()            # show the window

    sys.exit(app.exec())
