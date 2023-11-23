from PIL import Image
from PyQt6 import uic
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon, QFontDatabase, QPixmap
from PyQt6.QtWidgets import QMainWindow

import ctypes

from ctypes.wintypes import DWORD, ULONG
from ctypes import windll, c_bool, c_int, POINTER, Structure
from PyQt6.QtCore import Qt


class ACCENTPOLICY(Structure):
    _fields_ = [
        ('AccentState', DWORD),
        ('AccentFlags', DWORD),
        ('GradientColor', DWORD),
        ('AnimationId', DWORD),
    ]


class WINCOMPATTRDATA(Structure):
    _fields_ = [
        ('Attribute', DWORD),
        ('Data', POINTER(ACCENTPOLICY)),
        ('SizeOfData', ULONG),
    ]


SetWindowCompositionAttribute = windll.user32.SetWindowCompositionAttribute
SetWindowCompositionAttribute.restype = c_bool
SetWindowCompositionAttribute.argtypes = [c_int, POINTER(WINCOMPATTRDATA)]


class GUI(QMainWindow):
    def __init__(self, size, title, icon_path):
        super().__init__()
        self.setFixedSize(size[0], size[1])
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon_path))

    def setup_ui_form(self, ui_form):
        with open("data/styles/style.css") as style:
            uic.loadUi(f'data/{ui_form}.ui', self)
            QFontDatabase.addApplicationFont("data/fonts/Rubik/Rubik-Medium.ttf")
            self.setStyleSheet(style.read())

    def blur_background(self):
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        accent_policy = ACCENTPOLICY()
        accent_policy.AccentState = 3

        win_comp_attr_data = WINCOMPATTRDATA()
        win_comp_attr_data.Attribute = 19
        win_comp_attr_data.SizeOfData = ctypes.sizeof(accent_policy)
        win_comp_attr_data.Data = ctypes.pointer(accent_policy)

        SetWindowCompositionAttribute(c_int(int(self.winId())), ctypes.pointer(win_comp_attr_data))

    @staticmethod
    def exit_app():
        QCoreApplication.quit()

    def min_app(self):
        self.showMinimized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        try:
            if not self.old_pos:
                return
            delta = event.pos() - self.old_pos
            self.move(self.pos() + delta)
        except Exception:
            pass
