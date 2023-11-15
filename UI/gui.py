import os

from PIL.ImageQt import ImageQt
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFileDialog, QToolButton, QWidget, QVBoxLayout, QLabel, \
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox
from PyQt6.QtGui import QFontDatabase, QIcon, QPixmap
from PyQt6.QtCore import Qt, QCoreApplication

from PIL import Image

import ctypes
from ctypes.wintypes import DWORD, ULONG
from ctypes import windll, c_bool, c_int, POINTER, Structure

from Tools.PBR import PBRSet


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
    def __init__(self, cfg=None):
        super().__init__()
        self.setFixedSize(1024, 768)
        self.blur_background()
        self.cfg = cfg

        self.pbr_set = None
        self.load_cfg()

        self.setup_ui_form()
        app_icon = QIcon("UI/icons/app_icon.png")
        self.setWindowTitle("CS2 Workshop Tools Additions")
        self.setWindowIcon(app_icon)
        self.show()

    def load_cfg(self):
        if self.cfg is not None:
            self.finish_style = self.cfg.finish_style
            self.mode = self.cfg.mode
            self.saturation_value = self.cfg.saturation_value
            self.is_compensating = self.cfg.is_compensating
            self.compensation_coefficient = self.cfg.compensation_coefficient
            self.nm_min = self.cfg.nm_min
            self.nm_max = self.cfg.nm_max
            self.m_max = self.cfg.m_max

        else:
            self.finish_style = "Gunsmith"
            self.mode = "combined"
            self.saturation_value = 0.5
            self.is_compensating = True
            self.compensation_coefficient = 1.5
            self.nm_min = 55
            self.nm_max = 220
            self.m_max = 250

    def write_cfg(self):
        if self.cfg is not None:
            self.cfg.finish_style = self.finish_style
            self.cfg.mode = self.mode
            self.cfg.saturation_value = self.saturation_value
            self.cfg.is_compensating = self.is_compensating
            self.cfg.compensation_coefficient = self.compensation_coefficient
            self.cfg.nm_min = self.nm_min
            self.cfg.nm_max = self.nm_max
            self.cfg.m_min = self.m_min
            self.cfg.m_max = self.m_max

            self.cfg.write()

            self.status_label.setText("Default settings have been rewritten")

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

    def setup_ui_form(self):
        with open("UI/styles/style.css") as style:
            uic.loadUi('UI/ui_form.ui', self)
            QFontDatabase.addApplicationFont("UI/fonts/Rubik/Rubik-Medium.ttf")
            self.setStyleSheet(style.read())
            self.setup_widgets()
            self.set_image(self.background_image_label, self.background_layout, 733, 733,
                           Image.open('UI/background.png'), False)

    def setup_widgets(self):
        self.setalbedo_button = self.findChild(QToolButton, 'setalbedoButton')
        self.setmetallic_button = self.findChild(QToolButton, 'setmetallicButton')
        self.clamp_button = self.findChild(QPushButton, 'clampButton')
        self.validate_button = self.findChild(QPushButton, 'validateButton')
        self.save_button = self.findChild(QPushButton, 'saveButton')
        self.status_label = self.findChild(QLabel, 'statusLabel')
        self.albedo_path_input = self.findChild(QLineEdit, 'albedoPathInput')
        self.metallic_path_input = self.findChild(QLineEdit, 'metallicPathInput')
        self.metallic_path_input = self.findChild(QLineEdit, 'metallicPathInput')
        self.finish_style_box = self.findChild(QComboBox, 'finishStyleBox')
        self.is_compensating_box = self.findChild(QCheckBox, 'iscompensatingBox')
        self.saturation_limit_label = self.findChild(QLabel, 'saturationLabel')
        self.nm_range_label = self.findChild(QLabel, 'nmrangeLabel')
        self.m_range_label = self.findChild(QLabel, 'mrangeLabel')
        self.albedo_group = self.findChild(QGroupBox, 'albedoGroup')
        self.metallic_group = self.findChild(QGroupBox, 'metallicGroup')
        self.saturation_limit_box = self.findChild(QDoubleSpinBox, 'saturationValue')
        self.nm_min_box = self.findChild(QSpinBox, 'nmminBox')
        self.nm_max_box = self.findChild(QSpinBox, 'nmmaxBox')
        self.m_max_box = self.findChild(QSpinBox, 'mmaxBox')
        self.mode_box = self.findChild(QComboBox, 'finishStyleBox')
        self.albedo_icon = self.findChild(QPushButton, 'albedoIcon')
        self.metallic_icon = self.findChild(QPushButton, 'metallicIcon')
        self.author_label = self.findChild(QLabel, 'authorLabel')
        self.author_label.setOpenExternalLinks(True)
        self.rgb_info_label = self.findChild(QLabel, 'rgbinfoLink')
        self.rgb_info_label.setOpenExternalLinks(True)
        self.exit_button = self.findChild(QPushButton, 'exitButton')
        self.min_button = self.findChild(QPushButton, 'minButton')
        self.defaults_button = self.findChild(QPushButton, 'defaultsButton')

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

        self.setalbedo_button.clicked.connect(lambda: self.load_texture(self.albedo_icon, self.albedo_path_input, True))
        self.setmetallic_button.clicked.connect(lambda: self.load_texture(self.metallic_icon, self.metallic_path_input))
        self.clamp_button.clicked.connect(self.correct_albedo)
        self.validate_button.clicked.connect(self.verify_albedo)
        self.save_button.clicked.connect(self.save_textures)
        self.finish_style_box.currentIndexChanged.connect(self.mode_changed)
        self.is_compensating_box.stateChanged.connect(self.compensating_state_changed)
        self.exit_button.clicked.connect(self.exit_app)
        self.min_button.clicked.connect(self.min_app)
        self.nm_min_box.valueChanged.connect(self.range_changed)
        self.nm_max_box.valueChanged.connect(self.range_changed)
        self.m_max_box.valueChanged.connect(self.range_changed)
        self.defaults_button.clicked.connect(self.write_cfg)

        self.finish_style_box.setCurrentText(self.finish_style)
        self.is_compensating_box.setEnabled(self.is_compensating)
        self.nm_min_box.setValue(self.nm_min)
        self.nm_max_box.setValue(self.nm_max)
        self.m_max_box.setValue(self.m_max)

    def set_image(self, label, layout, width, height, image, remove_alpha=True):
        try:
            image = image.convert("RGBA")
            if remove_alpha:
                image.putalpha(Image.new('L', image.size, 255))

            pixmap = QPixmap.fromImage(ImageQt(image))
            pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
            layout.addWidget(label)
        except Exception:
            pass

    def set_icon(self, image, icon_widget):
        try:
            image = image.convert("RGBA")
            image.putalpha(Image.new('L', image.size, 255))
            pixmap = QPixmap.fromImage(ImageQt(image))
            icon_widget.setIcon(QIcon(pixmap))
        except Exception:
            pass

    def load_texture(self, icon, texture_input, is_set_image=False):
        texture_input.setStyleSheet("border-color: #343434;")
        try:
            filepath = QFileDialog.getOpenFileName(self, 'Open File', 'C:/', 'Image (*.tga;*.png;*.jpg;*.jpeg;*.jp2;*.bmp)')
            texture_input.setText(filepath[0])
            self.set_icon(Image.open(filepath[0]), icon)

            if is_set_image:
                self.set_image(self.active_image_label, self.active_image_layout, 650, 650, Image.open(filepath[0]))

            self.status_label.setText("Albedo texture was loaded successfully")
        except Exception:
            texture_input.setStyleSheet("border-color: #a03c3c;")

    def correct_albedo(self):
        valid_inputs = True
        if not (self.is_valid_image_path(self.albedo_path_input.text())):
            self.albedo_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if self.mode == "combined" and not (self.is_valid_image_path(self.metallic_path_input.text())):
            self.metallic_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if valid_inputs:
            albedomap = self.albedo_path_input.text()

            if self.mode == "combined":
                metallicmap = self.metallic_path_input.text()
            else:
                metallicmap = None

            if self.is_compensating:
                pass

            self.pbr_set = PBRSet(albedomap, metallicmap)

            self.pbr_set.correct_albedo(self.mode, self.is_compensating)

            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.pbr_set.albedo_corrected)

            self.status_label.setText("Albedo texture was corrected successfully")

        else:
            self.status_label.setText("Please make sure you have attached valid textures")

    def verify_albedo(self):
        valid_inputs = True
        if not (self.is_valid_image_path(self.albedo_path_input.text())):
            self.albedo_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if self.mode == "combined" and not (self.is_valid_image_path(self.metallic_path_input.text())):
            self.metallic_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if valid_inputs:
            albedo_map_path = self.albedo_path_input.text()

            if self.mode == "combined":
                metallic_map_path = self.metallic_path_input.text()
            else:
                metallic_map_path = None

            self.pbr_set = PBRSet(albedo_map_path, metallic_map_path)

            mismatched_pixels = self.pbr_set.verify_albedo(self.mode)

            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.pbr_set.albedo_verified)
            self.status_label.setText(f"{100 - round(mismatched_pixels / self.pbr_set.size() * 100)}% correct")

        else:
            self.status_label.setText("Please make sure you have attached valid textures")

    def save_textures(self):
        if self.pbr_set is not None:
            if self.pbr_set.albedo_corrected is not None or self.pbr_set.metallic_corrected is not None:
                try:
                    directory = os.path.dirname(self.albedo_path_input.text())
                    selected_directory = QFileDialog.getExistingDirectory(self, "Select a directory", directory)
                    self.pbr_set.save(selected_directory)
                    self.status_label.setText("Successfully saved")
                except Exception:
                    pass
        else:
            self.status_label.setText("Nothing to save")

    def compensating_state_changed(self):
        self.is_compensating = self.is_compensating_box.isChecked()

    def mode_changed(self):
        self.finish_style = self.finish_style_box.currentText()

        if self.finish_style == "Gunsmith":
            self.mode = "combined"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(True)
            self.is_compensating_box.setEnabled(True)
            self.metallic_icon.setEnabled(True)
            self.setmetallic_button.setEnabled(True)
            self.metallic_path_input.setEnabled(True)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(True)
            self.nm_min_box.setEnabled(True)
            self.nm_max_box.setEnabled(True)
            self.m_max_box.setEnabled(True)

        if self.finish_style == "Custom Paint Job":
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.is_compensating_box.setEnabled(True)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(False)
            self.nm_min_box.setEnabled(True)
            self.nm_max_box.setEnabled(True)
            self.m_max_box.setEnabled(False)

        if self.finish_style == "Patina":
            self.mode = "metallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(True)
            self.is_compensating_box.setEnabled(True)
            self.metallic_icon.setEnabled(False)
            self.setmetallic_button.setEnabled(False)
            self.metallic_path_input.setEnabled(False)
            self.nm_range_label.setEnabled(False)
            self.m_range_label.setEnabled(True)
            self.nm_min_box.setEnabled(False)
            self.nm_max_box.setEnabled(False)
            self.m_max_box.setEnabled(True)

        if self.finish_style == "Anodized Multicolored":
            self.mode = "metallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(True)
            self.metallic_icon.setEnabled(False)
            self.setmetallic_button.setEnabled(False)
            self.metallic_path_input.setEnabled(False)
            self.is_compensating_box.setEnabled(False)
            self.nm_range_label.setEnabled(False)
            self.m_range_label.setEnabled(True)
            self.nm_min_box.setEnabled(False)
            self.nm_max_box.setEnabled(False)
            self.m_max_box.setEnabled(True)

        if self.finish_style in ["Spray-Paint", "Hydrographic", "Anodized", "Anodized Airbrushed"]:
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.is_compensating_box.setEnabled(False)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(False)
            self.nm_min_box.setEnabled(True)
            self.nm_max_box.setEnabled(True)
            self.m_max_box.setEnabled(False)

    def range_changed(self):
        self.nm_min = self.nm_min_box.value()
        self.nm_max = self.nm_max_box.value()
        self.m_max = self.m_max_box.value()

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
