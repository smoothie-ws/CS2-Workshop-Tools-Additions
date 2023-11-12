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

from Tools.PBR import PBRAlbedo

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
            self.is_saturation_considered = self.cfg.is_saturation_considered
            self.saturation_value = self.cfg.saturation_value
            self.is_compensating = self.cfg.is_compensating
            self.compensation_coefficient = self.cfg.compensation_coefficient
            self.nm_min = self.cfg.nm_min
            self.nm_max = self.cfg.nm_max
            self.m_min = self.cfg.m_min
            self.m_max = self.cfg.m_max
            self.mhs_min = self.cfg.mhs_min
            self.mhs_max = self.cfg.mhs_max
        else:
            self.finish_style = "Gunsmith"
            self.mode = "combined"
            self.is_saturation_considered = True
            self.saturation_value = 0.5
            self.is_compensating = True
            self.compensation_coefficient = 1.5
            self.nm_min = 55
            self.nm_max = 220
            self.m_min = 180
            self.m_max = 250
            self.mhs_min = 90
            self.mhs_max = 250

    def write_cfg(self):
        if self.cfg is not None:
            self.cfg.finish_style = self.finish_style
            self.cfg.mode = self.mode
            self.cfg.is_saturation_considered = self.is_saturation_considered
            self.cfg.saturation_value = self.saturation_value
            self.cfg.is_compensating = self.is_compensating
            self.cfg.compensation_coefficient = self.compensation_coefficient
            self.cfg.nm_min = self.nm_min
            self.cfg.nm_max = self.nm_max
            self.cfg.m_min = self.m_min
            self.cfg.m_max = self.m_max
            self.cfg.mhs_min = self.mhs_min
            self.cfg.mhs_max = self.mhs_max

            self.cfg.write()

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
            self.show()
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
        self.is_saturation_box = self.findChild(QCheckBox, 'isSaturationBox')
        self.is_compensating_box = self.findChild(QCheckBox, 'isAoBox')
        self.saturation_limit_label = self.findChild(QLabel, 'saturationLabel')
        self.nm_range_label = self.findChild(QLabel, 'nmrangeLabel')
        self.m_range_label = self.findChild(QLabel, 'mrangeLabel')
        self.mhs_range_label = self.findChild(QLabel, 'mhsrangeLabel')
        self.albedo_group = self.findChild(QGroupBox, 'albedoGroup')
        self.metallic_group = self.findChild(QGroupBox, 'metallicGroup')
        self.ao_group = self.findChild(QGroupBox, 'aoGroup')
        self.ao_path_input = self.findChild(QLineEdit, 'aoPathInput')
        self.set_ao_button = self.findChild(QToolButton, 'setaoButton')
        self.saturation_limit_box = self.findChild(QDoubleSpinBox, 'saturationValue')
        self.ao_coefficient = self.findChild(QDoubleSpinBox, 'coefficientValue')
        self.nm_min_box = self.findChild(QSpinBox, 'nmminBox')
        self.nm_max_box = self.findChild(QSpinBox, 'nmmaxBox')
        self.m_min_box = self.findChild(QSpinBox, 'mminBox')
        self.m_max_box = self.findChild(QSpinBox, 'mmaxBox')
        self.mhs_min_box = self.findChild(QSpinBox, 'mhsminBox')
        self.mhs_max_box = self.findChild(QSpinBox, 'mhsmaxBox')
        self.mode_box = self.findChild(QComboBox, 'finishStyleBox')
        self.albedo_icon = self.findChild(QPushButton, 'albedoIcon')
        self.metallic_icon = self.findChild(QPushButton, 'metallicIcon')
        self.ao_icon = self.findChild(QPushButton, 'aoIcon')
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
        self.set_ao_button.clicked.connect(lambda: self.load_texture(self.ao_icon, self.ao_path_input))
        self.clamp_button.clicked.connect(self.correct_albedo)
        self.validate_button.clicked.connect(self.validate_albedo)
        self.save_button.clicked.connect(self.save_textures)
        self.is_saturation_box.stateChanged.connect(self.hs_state_changed)
        self.finish_style_box.currentIndexChanged.connect(self.mode_changed)
        self.is_compensating_box.stateChanged.connect(self.ao_state_changed)
        self.exit_button.clicked.connect(self.exit_app)
        self.min_button.clicked.connect(self.min_app)
        self.nm_min_box.valueChanged.connect(self.range_changed)
        self.nm_max_box.valueChanged.connect(self.range_changed)
        self.m_min_box.valueChanged.connect(self.range_changed)
        self.m_max_box.valueChanged.connect(self.range_changed)
        self.mhs_min_box.valueChanged.connect(self.range_changed)
        self.mhs_max_box.valueChanged.connect(self.range_changed)
        self.defaults_button.clicked.connect(self.write_cfg)

        self.finish_style_box.setCurrentText(self.finish_style)
        self.is_saturation_box.setEnabled(self.is_saturation_considered)
        self.saturation_limit_box.setValue(self.is_saturation_considered)
        self.is_compensating_box.setEnabled(self.is_compensating)
        self.ao_coefficient.setValue(self.compensation_coefficient)
        self.nm_min_box.setValue(self.nm_min)
        self.nm_max_box.setValue(self.nm_max)
        self.m_min_box.setValue(self.m_min)
        self.m_max_box.setValue(self.m_max)
        self.mhs_min_box.setValue(self.mhs_min)
        self.mhs_max_box.setValue(self.mhs_max)

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
        except Exception as e:
            print(e)

    def set_icon(self, image, icon_widget):
        try:
            image = image.convert("RGBA")
            image.putalpha(Image.new('L', image.size, 255))
            pixmap = QPixmap.fromImage(ImageQt(image))
            icon_widget.setIcon(QIcon(pixmap))
        except Exception as e:
            print(e)

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

        if self.is_compensating and not (self.is_valid_image_path(self.ao_path_input.text())):
            self.ao_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if self.mode == "combined" and not (self.is_valid_image_path(self.metallic_path_input.text())):
            self.metallic_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if valid_inputs == True:
            albedomap = self.albedo_path_input.text()

            if self.mode == "combined":
                metallicmap = self.metallic_path_input.text()
            else:
                metallicmap = None

            if self.is_compensating:
                aomap = self.ao_path_input.text()
            else:
                aomap = None

            self.pbr_set = PBRAlbedo([self.nm_min, self.nm_max, self.m_min, self.m_max, self.mhs_min, self.mhs_max], albedomap, metallicmap, aomap)

            self.pbr_set.clamp_rgb_range(self.mode, self.is_compensating, self.ao_coefficient.value(),
                                         self.is_saturation_box.isChecked(), self.saturation_limit_box.value())

            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.pbr_set.albedo_corrected)

            if self.is_compensating:
                self.status_label.setText("Albedo texture and AO map were corrected successfully")
            else:
                self.status_label.setText("Albedo texture was corrected successfully")

        else:
            self.status_label.setText("Please make sure you have attached valid textures")

    def validate_albedo(self):
        valid_inputs = True
        if not (self.is_valid_image_path(self.albedo_path_input.text())):
            self.albedo_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if self.mode == "combined" and not (self.is_valid_image_path(self.metallic_path_input.text())):
            self.metallic_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if valid_inputs == True:
            albedo_map_path = self.albedo_path_input.text()

            if self.mode == "combined":
                metallic_map_path = self.metallic_path_input.text()
            else:
                metallic_map_path = None

            self.pbr_set = PBRAlbedo(
                [self.nm_min.value(), self.nm_max.value(), self.m_min.value(), self.m_max.value(), self.mhs_min.value(),
                 self.mhs_max.value()], albedo_map_path, metallic_map_path)

            mismatched_pixels = self.pbr_set.validate_rgb_range(self.mode, self.is_saturation_box.isChecked(),
                                                                self.saturation_limit_box.value())

            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.pbr_set.albedo_validated)
            self.status_label.setText(f"{100 - round(mismatched_pixels / self.pbr_set.size() * 100)}% correct")

        else:
            self.status_label.setText("Please make sure you have attached valid textures")

    def save_textures(self):
        if self.pbr_set is not None:
            if self.pbr_set.albedo_corrected is not None or self.pbr_set.ao_corrected is not None:
                try:
                    directory = os.path.dirname(self.albedo_path_input.text())
                    # selected_directory = QFileDialog.getExistingDirectory(self, "Select a directory", directory)
                    self.pbr_set.save(directory)
                except Exception:
                    pass
        else:
            self.status_label.setText("Nothing to save")

    def hs_state_changed(self):
        self.is_saturation_considered = self.is_saturation_box.isChecked()
        self.saturation_limit_box.setEnabled(self.is_saturation_considered)
        self.mhs_min_box.setEnabled(self.is_saturation_considered)
        self.mhs_max_box.setEnabled(self.is_saturation_considered)
        self.saturation_limit_label.setEnabled(self.is_saturation_considered)
        self.mhs_range_label.setEnabled(self.is_saturation_considered)

    def ao_state_changed(self):
        self.is_compensating = self.is_compensating_box.isChecked()
        self.ao_group.setEnabled(self.is_compensating)

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
            self.mhs_range_label.setEnabled(True)
            self.nm_min_box.setEnabled(True)
            self.nm_max_box.setEnabled(True)
            self.m_min_box.setEnabled(True)
            self.m_max_box.setEnabled(True)
            self.mhs_min_box.setEnabled(True)
            self.mhs_max_box.setEnabled(True)

        if self.finish_style == "Custom Paint Job":
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.is_compensating_box.setEnabled(True)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(False)
            self.mhs_range_label.setEnabled(False)
            self.nm_min_box.setEnabled(True)
            self.nm_max_box.setEnabled(True)
            self.m_min_box.setEnabled(False)
            self.m_max_box.setEnabled(False)
            self.mhs_min_box.setEnabled(False)
            self.mhs_max_box.setEnabled(False)

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
            self.mhs_range_label.setEnabled(True)
            self.nm_min_box.setEnabled(False)
            self.nm_max_box.setEnabled(False)
            self.m_min_box.setEnabled(True)
            self.m_max_box.setEnabled(True)
            self.mhs_min_box.setEnabled(True)
            self.mhs_max_box.setEnabled(True)

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
            self.mhs_range_label.setEnabled(True)
            self.nm_min_box.setEnabled(False)
            self.nm_max_box.setEnabled(False)
            self.m_min_box.setEnabled(True)
            self.m_max_box.setEnabled(True)
            self.mhs_min_box.setEnabled(True)
            self.mhs_max_box.setEnabled(True)

        if self.finish_style in ["Spray-Paint", "Hydrographic", "Anodized", "Anodized Airbrushed"]:
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.is_compensating_box.setEnabled(False)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(False)
            self.mhs_range_label.setEnabled(False)
            self.nm_min_box.setEnabled(True)
            self.nm_max_box.setEnabled(True)
            self.m_min_box.setEnabled(False)
            self.m_max_box.setEnabled(False)
            self.mhs_min_box.setEnabled(False)
            self.mhs_max_box.setEnabled(False)

    def range_changed(self):
        self.nm_min = self.nm_min_box.value()
        self.nm_max = self.nm_max_box.value()
        self.m_min = self.m_min_box.value()
        self.m_max = self.m_max_box.value()
        self.mhs_min = self.mhs_min_box.value()
        self.mhs_max = self.mhs_max_box.value()

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
