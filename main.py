import os
import shutil
import subprocess
import zipfile
import requests
import re

from PyQt6 import uic
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
import sys


def extract_with_replace(zip_filename, extract_path='.'):
    for item in os.listdir(extract_path):
        if item != os.path.basename(__file__) and item != "config.cfg" and item != zip_filename:
            item_path = os.path.join(extract_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception:
                pass

    with zipfile.ZipFile(zip_filename, 'r') as archive:
        archive.extractall(extract_path)

    os.remove(zip_filename)


class UpdateWindow(QMainWindow):
    def __init__(self):
        super(UpdateWindow, self).__init__()
        self.setFixedSize(335, 160)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        with open("UI/styles/style.css") as style:
            uic.loadUi('UI/updatewinow_ui_form.ui', self)
            QFontDatabase.addApplicationFont("UI/fonts/Rubik/Rubik-Medium.ttf")
            self.setStyleSheet(style.read())

        self.update_button = self.findChild(QPushButton, 'updateButton')
        self.refuse_button = self.findChild(QPushButton, 'refuseButton')
        self.label = self.findChild(QLabel, 'Label')
        self.update_button.clicked.connect(self.accept_update)
        self.refuse_button.clicked.connect(self.exit)

    def exit(self):
        QCoreApplication.quit()
        subprocess.run(['python', 'app.py'])

    def accept_update(self):
        print("process started")
        self.label.setText("Downloading, please wait")
        self.update_button.setEnabled(False)
        self.refuse_button.setEnabled(False)
        # self.downloaded_filename = self.download(download_url.format(version=latest_version), f'cs2wta_{latest_version}.zip')
        # extract_with_replace(self.downloaded_filename)

    def download(self, url, filename):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return filename

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return

        delta = event.pos() - self.old_pos
        self.move(self.pos() + delta)


if __name__ == "__main__":
    version_check_url = 'https://api.github.com/repos/smoothie-ws/CS2-Workshop-Tools-Additions/releases/latest'
    download_url = 'https://github.com/smoothie-ws/CS2-Workshop-Tools-Additions/releases/download/{version}/cs2wta_{version}.zip'
    extract_path = './cs2wta_{version}/'
    destination_path = './'

    response = requests.get(version_check_url)
    response.raise_for_status()
    data = response.json()
    latest_version = data['tag_name']

    try:
        from Tools.CFG import CFG

        cfg = CFG("config.cfg")
        current_version = cfg.version
    except Exception:
        cfg = None
        current_version = 0.0

    if float(re.sub(r'[^\d.]', '', latest_version)) > float(current_version):

        app = QApplication(sys.argv)
        window = UpdateWindow()
        window.show()
        sys.exit(app.exec())

    else:
        exec(open('app.py').read())
