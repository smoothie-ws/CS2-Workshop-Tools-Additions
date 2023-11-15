import os
import shutil
import zipfile
import requests
import re

from PyQt6 import uic
from PyQt6.QtCore import Qt, QCoreApplication, QThread, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
import sys

from UI.gui import GUI


class UpdateThread(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
        self.update_signal.emit("Downloading...")

        # download_url = 'https://github.com/smoothie-ws/CS2-Workshop-Tools-Additions/releases/download/{version}/cs2wta_{version}.zip'
        # download_url = download_url.format(version=latest_version)
        #
        # response = requests.get(download_url, stream=True)
        # response.raise_for_status()
        # total_size = int(response.headers.get('content-length', 0))
        # block_size = 8192
        # downloaded = 0
        #
        # zip_filename = f'cs2wta_{latest_version}.zip'
        #
        # with open(zip_filename, 'wb') as file:
        #     for chunk in response.iter_content(chunk_size=block_size):
        #         file.write(chunk)
        #         downloaded += len(chunk)
        #         percent_complete = (downloaded / total_size) * 100
        for percent_complete in range(1000000):
                self.update_signal.emit(f"Downloading... {round(percent_complete / 10000)}%")

        # self.update_signal.emit("Extracting...")
        # extract_path = '.'
        #
        # for item in os.listdir(extract_path):
        #     if item != os.path.basename(__file__) and item != "config.cfg" and item != zip_filename:
        #         item_path = os.path.join(extract_path, item)
        #         try:
        #             if os.path.isfile(item_path) or os.path.islink(item_path):
        #                 os.unlink(item_path)
        #             elif os.path.isdir(item_path):
        #                 shutil.rmtree(item_path)
        #         except Exception:
        #             pass
        #
        # try:
        #     with zipfile.ZipFile(zip_filename, 'r') as archive:
        #         archive.extractall(extract_path)
        #
        #     os.remove(zip_filename)
        #
        #     self.update_signal.emit("Done")
        #
        # except Exception:
        self.update_signal.emit("Done")


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

        self.update_thread = UpdateThread()
        self.update_thread.update_signal.connect(self.handle_update_signal)

    def exit(self):
        QCoreApplication.quit()

    def accept_update(self):
        self.label.setText("Starting Update...")
        self.update_button.setVisible(False)
        self.refuse_button.setVisible(False)
        self.update_thread.start()

    def handle_update_signal(self, message):
        self.label.setText(message)

        if message == "Done":
            cfg = CFG("config.cfg")
            cfg.version = float(re.sub(r'[^\d.]', '', latest_version))
            cfg.write()

            QCoreApplication.quit()

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


def run_application():

    app = QApplication(sys.argv)

    try:
        cfg = CFG("config.cfg")
        window = GUI(cfg)
    except Exception:
        window = GUI()

    sys.exit(app.exec())


if __name__ == "__main__":
    version_check_url = 'https://api.github.com/repos/smoothie-ws/CS2-Workshop-Tools-Additions/releases/latest'

    try:
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

            try:
                from Tools.CFG import CFG
                cfg = CFG("config.cfg")
                app_window = GUI(cfg)
                app_window.hide()
            except Exception:
                app_window = GUI()
                app_window.hide()

            window.show()
            app.exec()

            app_window.show()
            app.exec()
        else:
            run_application()

    except Exception:
        run_application()
