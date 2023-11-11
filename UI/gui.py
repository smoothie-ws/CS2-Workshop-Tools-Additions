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
        self.consider_hs = True
        self.compensate = True
        self.pbr_set = None

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
            QFontDatabase.addApplicationFont("UI/fonts/Rubik/Rubik-Medium.ttf")
            self.setStyleSheet(style.read())
            self.show()
            self.add_menu()
            self.setup_widgets()
            self.set_image(self.background_image_label, self.background_layout, 733, 733, Image.open('UI/background.png'), False)

    def add_menu(self):
        self.exit_button = self.findChild(QPushButton, 'exitButton')
        self.min_button = self.findChild(QPushButton, 'minButton')

        self.exit_button.clicked.connect(self.exit_app)
        self.min_button.clicked.connect(self.min_app)

    def set_image(self, label, layout, width, height, image, remove_alpha=True):

            if image is not None and remove_alpha and image.mode != "P":
                alpha_image = Image.new('L', image.size, 255)
                image.putalpha(alpha_image)

            qimage = ImageQt(image)
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
            layout.addWidget(label)

    def set_icon(self, image, icon_widget):
        if image is not None:
            if image.mode != "P":
                alpha_image = Image.new('L', image.size, 255)
                image.putalpha(alpha_image)

        qimage = ImageQt(image)
        qpixmap = QPixmap.fromImage(qimage)
        icon_widget.setIcon(QIcon(qpixmap))

    def setup_widgets(self):
        self.setalbedo_button = self.findChild(QToolButton, 'setalbedoButton')
        self.setmetallic_button = self.findChild(QToolButton, 'setmetallicButton')
        self.clamp_button = self.findChild(QPushButton, 'clampButton')
        self.validate_button = self.findChild(QPushButton, 'validateButton')
        self.save_button = self.findChild(QPushButton, 'saveButton')
        self.validation_result_label = self.findChild(QLabel, 'validationResultLabel')
        self.albedoPath_input = self.findChild(QLineEdit, 'albedoPathInput')
        self.metallicPath_input = self.findChild(QLineEdit, 'metallicPathInput')
        self.metallicPath_input = self.findChild(QLineEdit, 'metallicPathInput')
        self.finishstyle_box = self.findChild(QComboBox, 'finishStyleBox')
        self.is_saturation_box = self.findChild(QCheckBox, 'isSaturationBox')
        self.is_compensating = self.findChild(QCheckBox, 'isAoBox')
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
        self.nm_min = self.findChild(QSpinBox, 'nmminBox')
        self.nm_max = self.findChild(QSpinBox, 'nmmaxBox')
        self.m_min = self.findChild(QSpinBox, 'mminBox')
        self.m_max = self.findChild(QSpinBox, 'mmaxBox')
        self.mhs_min = self.findChild(QSpinBox, 'mhsminBox')
        self.mhs_max = self.findChild(QSpinBox, 'mhsmaxBox')
        self.mode_box = self.findChild(QComboBox, 'finishStyleBox')
        self.albedo_icon = self.findChild(QPushButton, 'albedoIcon')
        self.metallic_icon = self.findChild(QPushButton, 'metallicIcon')
        self.ao_icon = self.findChild(QPushButton, 'aoIcon')
        self.author_label = self.findChild(QLabel, 'authorLabel')
        self.author_label.setOpenExternalLinks(True)
        self.rgb_info_label = self.findChild(QLabel, 'rgbinfoLink')
        self.rgb_info_label.setOpenExternalLinks(True)

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


        self.setalbedo_button.clicked.connect(self.set_albedomap)
        self.setmetallic_button.clicked.connect(self.set_metallicmap)
        self.set_ao_button.clicked.connect(self.set_aomap)
        self.clamp_button.clicked.connect(self.correct_albedo)
        self.validate_button.clicked.connect(self.validate_albedo)
        self.save_button.clicked.connect(self.save_textures)
        self.is_saturation_box.stateChanged.connect(self.hs_state_changed)
        self.finishstyle_box.currentIndexChanged.connect(self.mode_changed)
        self.is_compensating.stateChanged.connect(self.ao_state_changed)

    def set_albedomap(self):
        try:
            self.albedoPath_input.setStyleSheet("border-color: #343434;")
            albedomap = QFileDialog.getOpenFileName(self, 'Open File', 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo', 'Image (*.tga;*.png;*.jpg;*.jpeg;*.jp2;*.bmp)')
            self.albedoPath_input.setText(albedomap[0])
            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, Image.open(albedomap[0]))
            self.validation_result_label.setText("Albedo texture was loaded successfully")
            self.set_icon(Image.open(albedomap[0]), self.albedo_icon)
        except Exception:
            pass

    def set_metallicmap(self):
        try:
            self.metallicPath_input.setStyleSheet("border-color: #343434;")
            metallicmap = QFileDialog.getOpenFileName(self, 'Open File', 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo', 'Image (*.tga;*.png;*.jpg;*.jpeg;*.jp2;*.bmp)')
            self.metallicPath_input.setText(metallicmap[0])
            self.validation_result_label.setText("Material mask was loaded successfully")
            self.set_icon(Image.open(metallicmap[0]), self.metallic_icon)
        except Exception:
            pass

    def set_aomap(self):
        try:
            self.ao_path_input.setStyleSheet("border-color: #343434;")
            aomap = QFileDialog.getOpenFileName(self, 'Open File', 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo', 'Image (*.tga;*.png;*.jpg;*.jpeg;*.jp2;*.bmp)')
            self.ao_path_input.setText(aomap[0])
            self.validation_result_label.setText("AO map was loaded successfully")
            self.set_icon(Image.open(aomap[0]), self.ao_icon)
        except Exception:
            pass

    def correct_albedo(self):
        valid_inputs = True
        if not(self.is_valid_image_path(self.albedoPath_input.text())):
            self.albedoPath_input.setStyleSheet("border-color: #a03c3c;")
            self.validation_result_label.setText("Please make sure you have attached valid textures")
            valid_inputs = False

        if self.compensate and not(self.is_valid_image_path(self.ao_path_input.text())):
            self.ao_path_input.setStyleSheet("border-color: #a03c3c;")
            self.validation_result_label.setText("Please make sure you have attached valid textures")
            valid_inputs = False

        if self.mode == "combined" and not(self.is_valid_image_path(self.metallicPath_input.text())):
            self.metallicPath_input.setStyleSheet("border-color: #a03c3c;")
            self.validation_result_label.setText("Please make sure you have attached valid textures")
            valid_inputs = False

        if valid_inputs == True:
            albedomap = self.albedoPath_input.text()

            if self.mode == "combined":
                metallicmap = self.metallicPath_input.text()
            else:
                metallicmap = None

            if self.compensate:
                aomap = self.ao_path_input.text()
            else:
                aomap = None

            self.pbr_set = PBRAlbedo([self.nm_min.value(), self.nm_max.value(), self.m_min.value(), self.m_max.value(), self.mhs_min.value(), self.mhs_max.value()],albedomap, metallicmap, aomap)
            self.pbr_set.clamp_rgb_range(self.mode, self.compensate, self.ao_coefficient.value(), self.is_saturation_box.isChecked(), self.saturation_limit_box.value())

            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.pbr_set.albedo_corrected)

            if self.compensate:
                self.validation_result_label.setText("Albedo texture and AO map were corrected successfully")
            else:
                self.validation_result_label.setText("Albedo texture was corrected successfully")

    def validate_albedo(self):
        self.ao_path_input.setStyleSheet("border-color: #343434;")
        valid_inputs = True
        if not(self.is_valid_image_path(self.albedoPath_input.text())):
            self.albedoPath_input.setStyleSheet("border-color: #a03c3c;")
            self.validation_result_label.setText("Please make sure you have attached valid textures")
            valid_inputs = False

        if self.mode == "combined" and not(self.is_valid_image_path(self.metallicPath_input.text())):
            self.metallicPath_input.setStyleSheet("border-color: #a03c3c;")
            self.validation_result_label.setText("Please make sure you have attached valid textures")
            valid_inputs = False

        if valid_inputs == True:
            albedomap = self.albedoPath_input.text()

            if self.mode == "combined":
                metallicmap = self.metallicPath_input.text()
            else:
                metallicmap = None

            self.pbr_set = PBRAlbedo([self.nm_min.value(), self.nm_max.value(), self.m_min.value(), self.m_max.value(), self.mhs_min.value(), self.mhs_max.value()],albedomap, metallicmap)
            mismatched_pixels = self.pbr_set.validate_rgb_range(self.mode, self.is_saturation_box.isChecked(), self.saturation_limit_box.value())
            self.set_image(self.active_image_label, self.active_image_layout,650, 650, self.pbr_set.albedo_validated)
            self.validation_result_label.setText(f"{100 - round(mismatched_pixels / self.pbr_set.size() * 100)}% correct")

    def save_textures(self):
        if self.pbr_set is not None:
            if self.pbr_set.albedo_corrected is not None or self.pbr_set.ao_corrected is not None:
                try:
                    directory = os.path.dirname(self.albedoPath_input.text())
                    # selected_directory = QFileDialog.getExistingDirectory(self, "Select a directory", directory)
                    self.pbr_set.save(directory)
                except Exception:
                    pass
        else:
            self.validation_result_label.setText("Nothing to save")


    def hs_state_changed(self):
        self.consider_hs = self.is_saturation_box.isChecked()
        self.saturation_limit_box.setEnabled(self.consider_hs)
        self.mhs_min.setEnabled(self.consider_hs)
        self.mhs_max.setEnabled(self.consider_hs)
        self.saturation_limit_label.setEnabled(self.consider_hs)
        self.mhs_range_label.setEnabled(self.consider_hs)

    def ao_state_changed(self):
        self.compensate = self.is_compensating.isChecked()
        self.ao_group.setEnabled(self.compensate)

    def mode_changed(self):
        if self.finishstyle_box.currentText() == "Gunsmith":
            self.mode = "combined"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(True)
            self.ao_group.setEnabled(True)
            self.metallic_icon.setEnabled(True)
            self.setmetallic_button.setEnabled(True)
            self.metallicPath_input.setEnabled(True)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(True)
            self.mhs_range_label.setEnabled(True)
            self.nm_min.setEnabled(True)
            self.nm_max.setEnabled(True)
            self.m_min.setEnabled(True)
            self.m_max.setEnabled(True)
            self.mhs_min.setEnabled(True)
            self.mhs_max.setEnabled(True)


        if self.finishstyle_box.currentText() == "Custom Paint Job":
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.ao_group.setEnabled(True)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(False)
            self.mhs_range_label.setEnabled(False)
            self.nm_min.setEnabled(True)
            self.nm_max.setEnabled(True)
            self.m_min.setEnabled(False)
            self.m_max.setEnabled(False)
            self.mhs_min.setEnabled(False)
            self.mhs_max.setEnabled(False)

        if self.finishstyle_box.currentText() == "Patina":
            self.mode = "metallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(True)
            self.ao_group.setEnabled(True)
            self.metallic_icon.setEnabled(False)
            self.setmetallic_button.setEnabled(False)
            self.metallicPath_input.setEnabled(False)
            self.nm_range_label.setEnabled(False)
            self.m_range_label.setEnabled(True)
            self.mhs_range_label.setEnabled(True)
            self.nm_min.setEnabled(False)
            self.nm_max.setEnabled(False)
            self.m_min.setEnabled(True)
            self.m_max.setEnabled(True)
            self.mhs_min.setEnabled(True)
            self.mhs_max.setEnabled(True)

        if self.finishstyle_box.currentText() == "Anodized Multicolored":
            self.mode = "metallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(True)
            self.ao_group.setEnabled(False)
            self.metallic_icon.setEnabled(False)
            self.setmetallic_button.setEnabled(False)
            self.metallicPath_input.setEnabled(False)
            self.nm_range_label.setEnabled(False)
            self.m_range_label.setEnabled(True)
            self.mhs_range_label.setEnabled(True)
            self.nm_min.setEnabled(False)
            self.nm_max.setEnabled(False)
            self.m_min.setEnabled(True)
            self.m_max.setEnabled(True)
            self.mhs_min.setEnabled(True)
            self.mhs_max.setEnabled(True)

        if self.finishstyle_box.currentText() in ["Spray-Paint", "Hydrographic", "Anodized", "Anodized Airbrushed"]:
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.ao_group.setEnabled(False)
            self.nm_range_label.setEnabled(True)
            self.m_range_label.setEnabled(False)
            self.mhs_range_label.setEnabled(False)
            self.nm_min.setEnabled(True)
            self.nm_max.setEnabled(True)
            self.m_min.setEnabled(False)
            self.m_max.setEnabled(False)
            self.mhs_min.setEnabled(False)
            self.mhs_max.setEnabled(False)

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

