from PyQt6 import uic, QtGui
from PyQt6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFileDialog, QToolButton, QWidget, QVBoxLayout, QLabel, \
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QStackedWidget
from PyQt6.QtGui import QFontDatabase, QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt, QCoreApplication
from superqt import QRangeSlider

from PIL import Image

import ctypes
from ctypes.wintypes import DWORD, ULONG
from ctypes import windll, c_bool, c_int, POINTER, Structure

from Tools.PBR import PBRAlbedo

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
        self.mode = "combined"
        self.consider_hs = False
        self.compensate = False
        self.hs_definition = 0.70

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
            self.setup_widgets()

            self.background = self.findChild(QWidget, 'background')
            self.background_layout = QVBoxLayout(self.background)
            self.background_layout.setContentsMargins(0, 0, 0, 0)
            self.background_image_label = QLabel()
            self.background_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.active_image = self.findChild(QWidget, 'image_plane')
            self.active_image_layout = QVBoxLayout(self.active_image)
            self.active_image_layout.setContentsMargins(0, 0, 0, 0)
            self.active_image_label = QLabel()
            self.active_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.set_image(self.background_image_label, self.background_layout, 733, 733, 'UI/background.png')

    def add_menu(self):
        self.exit_button = self.findChild(QPushButton, 'exitButton')
        self.min_button = self.findChild(QPushButton, 'minButton')

        self.exit_button.clicked.connect(self.exit_app)
        self.min_button.clicked.connect(self.min_app)

    def set_image(self, label, layout, width, height, image_path):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)
        layout.addWidget(label)

    def setup_widgets(self):
        self.setalbedo_button = self.findChild(QToolButton, 'setalbedoButton')
        self.setmetallic_button = self.findChild(QToolButton, 'setmetallicButton')
        self.clamp_button = self.findChild(QPushButton, 'clampButton')
        self.validate_button = self.findChild(QPushButton, 'validateButton')
        self.validation_result_label = self.findChild(QLabel, 'validationResultLabel')
        self.albedoPath_input = self.findChild(QLineEdit, 'albedoPathInput')
        self.metallicPath_input = self.findChild(QLineEdit, 'metallicPathInput')
        self.metallicPath_input = self.findChild(QLineEdit, 'metallicPathInput')
        self.finishstyle_box = self.findChild(QComboBox, 'finishStyleBox')
        self.is_saturation_box = self.findChild(QCheckBox, 'isSaturationBox')
        self.is_compensating = self.findChild(QCheckBox, 'isAoBox')
        self.saturation_limit_label = self.findChild(QLabel, 'saturationLabel')
        self.metallic_path_label = self.findChild(QLabel, 'metallicPathLabel')
        self.ao_path_label = self.findChild(QLabel, 'aoPathLabel')
        self.m_range_label = self.findChild(QLabel, 'mrangeLabel')
        self.mhs_range_label = self.findChild(QLabel, 'mhsrangeLabel')



        self.ao_path_label = self.findChild(QLabel, 'aoPathLabel')
        self.ao_path_input = self.findChild(QLineEdit, 'aoPathInput')
        self.set_ao_button = self.findChild(QToolButton, 'setaoButton')
        self.saturation_limit_box = self.findChild(QDoubleSpinBox, 'saturationValue')
        self.mode_box = self.findChild(QComboBox, 'finishStyleBox')

        self.saturation_limit_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
        self.saturation_limit_box.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
        self.ao_path_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
        self.set_ao_button.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
        self.ao_path_input.setStyleSheet("color: rgba(164, 164, 164, 0.418);")

        self.setalbedo_button.clicked.connect(self.set_albedomap)
        self.setmetallic_button.clicked.connect(self.set_metallicmap)
        self.set_ao_button.clicked.connect(self.set_aomap)
        self.clamp_button.clicked.connect(self.correct_albedo)
        self.validate_button.clicked.connect(self.validate_albedo)
        self.is_saturation_box.stateChanged.connect(self.hs_state_changed)
        self.finishstyle_box.currentIndexChanged.connect(self.mode_changed)
        self.is_compensating.stateChanged.connect(self.ao_state_changed)

    def set_albedomap(self):
        self.albedoPath_input.setStyleSheet("border-color: #343434;")
        albedomap = QFileDialog.getOpenFileName(self, 'Open File', '/Users', 'Targa (*.tga);;PNG (*.png)')
        self.albedoPath_input.setText(albedomap[0])
        self.set_image(self.active_image_label, self.active_image_layout, 650, 650, albedomap[0])
        self.validation_result_label.setText("Albedo texture was loaded successfully")

    def set_metallicmap(self):
        self.metallicPath_input.setStyleSheet("border-color: #343434;")
        metallicmap = QFileDialog.getOpenFileName(self, 'Open File', '/Users', 'Targa (*.tga);;PNG (*.png)')
        self.metallicPath_input.setText(metallicmap[0])
        self.validation_result_label.setText("Metallic texture was loaded successfully")

    def set_aomap(self):
        self.ao_path_input.setStyleSheet("border-color: #343434;")
        aomap = QFileDialog.getOpenFileName(self, 'Open File', '/Users', 'Targa (*.tga);;PNG (*.png)')
        self.ao_path_input.setText(aomap[0])
        self.validation_result_label.setText("AO map was loaded successfully")

    def correct_albedo(self):
        if not(self.is_valid_image_path(self.albedoPath_input.text())):
            self.albedoPath_input.setStyleSheet("border-color: #a03c3c;")

        if not(self.is_valid_image_path(self.metallicPath_input.text())) and self.finishstyle_box.currentText() == "Gunsmith":
            self.metallicPath_input.setStyleSheet("border-color: #a03c3c;")

        if not(self.is_valid_image_path(self.ao_path_input.text())) and self.is_compensating.isChecked():
            self.ao_path_input.setStyleSheet("border-color: #a03c3c;")

        elif (self.is_valid_image_path(self.albedoPath_input.text()) and self.is_valid_image_path(self.metallicPath_input.text()) and not self.is_compensating.isChecked()) or (self.is_valid_image_path(self.albedoPath_input.text()) and self.is_valid_image_path(self.metallicPath_input.text()) and self.is_valid_image_path(self.ao_path_input.text()) and self.is_compensating.isChecked()):
            albedomap = self.albedoPath_input.text()
            metallicmap = self.metallicPath_input.text()
            if self.is_valid_image_path(self.ao_path_input.text()):
                aomap = self.ao_path_input.text()
            albedo = PBRAlbedo(albedomap, metallicmap, aomap)
            albedo.clamp_rgb_range(self.mode, self.is_compensating.isChecked(), self.is_saturation_box.isChecked(), self.saturation_limit_box.value())

            if not self.is_compensating.isChecked():
                self.set_image(self.active_image_label, self.active_image_layout,650, 650, albedo.save("albedo_corrected"))
                self.validation_result_label.setText("Albedo texture was corrected successfully")
            else:
                albedo.save("ao_corrected")
                self.set_image(self.active_image_label, self.active_image_layout,650, 650, albedo.save("albedo_corrected"))
                self.validation_result_label.setText("Albedo texture and AO map were corrected successfully")

    def validate_albedo(self):
        if not(self.is_valid_image_path(self.albedoPath_input.text())):
            self.albedoPath_input.setStyleSheet("border-color: #a03c3c;")

        if not(self.is_valid_image_path(self.metallicPath_input.text())) and self.finishstyle_box.currentText() == "Gunsmith":
            self.metallicPath_input.setStyleSheet("border-color: #a03c3c;")

        elif self.is_valid_image_path(self.albedoPath_input.text()) and self.is_valid_image_path(self.metallicPath_input.text()):
            albedomap = self.albedoPath_input.text()
            metallicmap = self.metallicPath_input.text()
            albedo = PBRAlbedo(albedomap, metallicmap)
            mismatched_pixels = albedo.validate_rgb_range(self.mode, self.is_saturation_box.isChecked(), self.saturation_limit_box.value())
            self.set_image(self.active_image_label, self.active_image_layout,650, 650, albedo.save("albedo_validated"))
            self.validation_result_label.setText(f"{100 - round(mismatched_pixels / albedo.size() * 100)}% correct")

    def hs_state_changed(self):
        self.consider_hs = self.is_saturation_box.isChecked()
        if self.consider_hs:
            self.saturation_limit_label.setStyleSheet("color: #A4A4A4;")
            self.saturation_limit_box.setStyleSheet("color: #A4A4A4;")
        else:
            self.saturation_limit_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
            self.saturation_limit_box.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
        self.saturation_limit_box.setEnabled(self.consider_hs)

    def ao_state_changed(self):
        self.compensate = self.is_compensating.isChecked()
        if self.compensate:
            self.ao_path_label.setStyleSheet("color: #A4A4A4;")
            self.ao_path_input.setStyleSheet("color: #A4A4A4;")
            self.set_ao_button.setStyleSheet("color: #A4A4A4;")
        else:
            self.ao_path_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
            self.set_ao_button.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
            self.ao_path_input.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
        self.ao_path_input.setEnabled(self.compensate)
        self.set_ao_button.setEnabled(self.compensate)

    def mode_changed(self):
        if self.finishstyle_box.currentText() == "Gunsmith":
            self.mode = "combined"
            self.metallic_path_label.setStyleSheet("color: #C4C4C4;")
            self.metallicPath_input.setEnabled(True)
            self.setmetallic_button.setEnabled(True)
            self.is_saturation_box.setEnabled(True)
            self.is_saturation_box.setStyleSheet("color: #C4C4C4;")
            self.is_compensating.setEnabled(True)
            self.m_range_label.setStyleSheet("color: #C4C4C4;")
            self.mhs_range_label.setStyleSheet("color: #C4C4C4;")

        if self.finishstyle_box.currentText() == "Custom Paint Job":
            self.mode = "nonmetallic"
            self.metallic_path_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
            self.metallicPath_input.setEnabled(False)
            self.setmetallic_button.setEnabled(False)
            self.is_saturation_box.setEnabled(False)
            self.is_saturation_box.setChecked(False)
            self.is_saturation_box.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
            self.is_compensating.setEnabled(True)
            self.m_range_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")
            self.mhs_range_label.setStyleSheet("color: rgba(164, 164, 164, 0.418);")

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

    @staticmethod
    def is_valid_image_path(image_path):
        try:
            with Image.open(image_path) as img:
                return True
        except (FileNotFoundError, IsADirectoryError):
            return False
        except:
            return False

