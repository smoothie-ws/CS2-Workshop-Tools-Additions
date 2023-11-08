from PyQt6 import uic, QtGui
from PyQt6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFileDialog, QToolButton, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFontDatabase, QIcon, QPixmap
from PyQt6.QtCore import Qt, QCoreApplication

import ctypes
from ctypes.wintypes import DWORD, ULONG
from ctypes import windll, c_bool, c_int, POINTER, Structure

from Processing.pbrtools import PBRMap

class AccentPolicy(Structure):
    _fields_ = [
        ('AccentState', DWORD),
        ('AccentFlags', DWORD),
        ('GradientColor', DWORD),
        ('AnimationId', DWORD),
    ]


class WINCOMPATTRDATA(Structure):
    _fields_ = [
        ('Attribute', DWORD),
        ('Data', POINTER(AccentPolicy)),
        ('SizeOfData', ULONG),
    ]


SetWindowCompositionAttribute = windll.user32.SetWindowCompositionAttribute
SetWindowCompositionAttribute.restype = c_bool
SetWindowCompositionAttribute.argtypes = [c_int, POINTER(WINCOMPATTRDATA)]

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1024, 768)
        self.blur_background()
        self.setup_ui_form()
        app_icon = QIcon("UI/icons/app_icon.png")
        self.setWindowTitle("Automatic PBR Fixer for CS2 Weapon Finishes")
        self.setWindowIcon(app_icon)
        self.set_background_image


    def blur_background(self):
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        accent_policy = AccentPolicy()
        accent_policy.AccentState = 3

        win_comp_attr_data = WINCOMPATTRDATA()
        win_comp_attr_data.Attribute = 19
        win_comp_attr_data.SizeOfData = ctypes.sizeof(accent_policy)
        win_comp_attr_data.Data = ctypes.pointer(accent_policy)

        SetWindowCompositionAttribute(c_int(int(self.winId())), ctypes.pointer(win_comp_attr_data))

    def setup_ui_form(self):
        with open("UI/styles/style.css") as style:
            uic.loadUi('UI/ui_form.ui', self)
            QFontDatabase.addApplicationFont("UI/fonts/Roboto/Roboto-Medium.ttf")
            self.setStyleSheet(style.read())
            self.show()
            self.add_menu()
            self.connect_buttons()
            self.background = self.findChild(QWidget, 'background')
            self.background_layout = QVBoxLayout(self.background)
            self.background_image_label = QLabel()
            self.background_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.set_background_image('UI/background.png')

    def add_menu(self):
        self.exit_button = self.findChild(QPushButton, 'exitButton')
        self.min_button = self.findChild(QPushButton, 'minButton')

        self.exit_button.clicked.connect(self.exit_app)
        self.min_button.clicked.connect(self.min_app)

    def set_background_image(self, image_path):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.background_image_label.setPixmap(pixmap)
        self.background_layout.addWidget(self.background_image_label)

    def connect_buttons(self):
        self.setalbedo_button = self.findChild(QToolButton, 'setalbedoButton')
        self.setmetallic_button = self.findChild(QToolButton, 'setmetallicButton')
        self.clamp_button = self.findChild(QPushButton, 'clampButton')
        self.albedoPath_input = self.findChild(QLineEdit, 'albedoPathInput')
        self.metallicPath_input = self.findChild(QLineEdit, 'metallicPathInput')

        self.setalbedo_button.clicked.connect(self.set_albedomap)
        self.setmetallic_button.clicked.connect(self.set_metallicmap)
        self.clamp_button.clicked.connect(self.fixPBR)

    def set_albedomap(self):
        albedomap = QFileDialog.getOpenFileName(self, 'Open File', '/Users', 'Targa (*.tga);;PNG (*.png)')
        self.albedoPath_input.setText(albedomap[0])
        self.set_background_image(albedomap[0])

    def set_metallicmap(self):
        metallicmap = QFileDialog.getOpenFileName(self, 'Open File', '/Users', 'Targa (*.tga);;PNG (*.png)')
        self.metallicPath_input.setText(metallicmap[0])

    def fixPBR(self):
        albedomap = self.albedoPath_input.text()
        metallicmap = self.metallicPath_input.text()
        pbr_corrected = PBRMap(albedomap, metallicmap)
        pbr_corrected.range_clamp()
        self.set_background_image(pbr_corrected.save())

    def exit_app(self):
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
        if not self.old_pos:
            return

        delta = event.pos() - self.old_pos
        self.move(self.pos() + delta)
