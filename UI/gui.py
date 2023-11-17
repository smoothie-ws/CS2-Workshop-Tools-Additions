import os

from PIL.ImageQt import ImageQt
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFileDialog, QToolButton, QWidget, QVBoxLayout, QLabel, \
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox
from PyQt6.QtGui import QFontDatabase, QIcon, QPixmap
from PyQt6.QtCore import Qt, QCoreApplication, QThread, pyqtSignal

from PIL import Image, ImageChops

import ctypes
from ctypes.wintypes import DWORD, ULONG
from ctypes import windll, c_bool, c_int, POINTER, Structure

from Tools.CFG import CFG
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


class ProcessingThread(QThread):
    signal = pyqtSignal(str)

    type = "correcting"
    mode = "combined"
    is_compensating = False
    compensation_coefficient = 1.0
    albedo = None
    metallic = None
    albedo_corrected = None
    albedo_verified = None
    mismatched_pixels = 0
    limit_values = None

    def run(self):
        self.signal.emit("Processing...")

        pbr_set = PBRSet(self.albedo, self.metallic)
        if self.type == "correcting":
            pbr_set.correct_albedo(self.mode, self.limit_values, self.is_compensating, self.compensation_coefficient)
            self.albedo_corrected = pbr_set.albedo_corrected
        elif self.type == "verifying":
            self.mismatched_pixels = pbr_set.verify_albedo(self.limit_values, self.mode)
            self.albedo_verified = pbr_set.albedo_verified

        self.signal.emit("Done")


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1024, 768)
        self.blur_background()
        self.pbr_set = None
        self.active_image = None
        self.albedo_image = None
        self.metallic_image = None
        self.ao_image = None
        self.load_cfg()
        self.setup_ui_form()
        app_icon = QIcon("UI/icons/app_icon.png")
        self.setWindowTitle("CS2 Workshop Tools Additions")
        self.setWindowIcon(app_icon)
        self.show()

        self.processing_thread = ProcessingThread()
        self.processing_thread.signal.connect(self.handle_processing_signal)

    def load_cfg(self):
        cfg = CFG("config.cfg")
        self.is_compensating = cfg.is_compensating
        self.compensation_coefficient = cfg.compensation_coefficient
        self.l_min = cfg.l_min
        self.l_max = cfg.l_max
        self.b_limit = cfg.b_limit
        self.finish_style = cfg.finish_style
        self.mode = cfg.mode

    def write_cfg(self):
        cfg = CFG("config.cfg")

        cfg.finish_style = self.finish_style
        cfg.mode = self.mode
        cfg.is_compensating = self.is_compensating
        cfg.compensation_coefficient = self.compensation_coefficient
        cfg.l_min = self.l_min
        cfg.l_max = self.l_max
        cfg.b_limit = self.b_limit

        cfg.write()

        self.status_label.setText("Default settings have been rewritten")

    def handle_processing_signal(self, message):
        self.status_label.setStyleSheet("color: #a03c3c;")
        self.status_label.setText(message)

        if message == "Done":
            self.pbr_set = PBRSet(self.processing_thread.albedo, self.processing_thread.metallic)
            if self.processing_thread.type == "correcting":
                self.status_label.setText("Albedo texture was corrected successfully")
                self.status_label.setStyleSheet("color: rgba(168, 168, 168, 0.582);")

                self.central_widget.setEnabled(True)

                self.pbr_set.albedo_corrected = self.processing_thread.albedo_corrected

                self.active_image = self.pbr_set.albedo_corrected.convert("RGB")

                self.toggle_ao()

            elif self.processing_thread.type == "verifying":
                mismatched_pixels = self.processing_thread.mismatched_pixels

                self.status_label.setText(f"{100 - round(mismatched_pixels / self.pbr_set.size() * 100)}% correct")
                self.status_label.setStyleSheet("color: rgba(168, 168, 168, 0.582);")

                self.central_widget.setEnabled(True)

                self.pbr_set.albedo_verified = self.processing_thread.albedo_verified

                self.active_image = self.pbr_set.albedo_verified.convert("RGB")

                self.toggle_ao()

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
        self.central_widget = self.findChild(QWidget, 'centralwidget')

        self.exit_button = self.findChild(QPushButton, 'exitButton')
        self.min_button = self.findChild(QPushButton, 'minButton')
        self.author_label = self.findChild(QLabel, 'authorLabel')
        self.author_label.setOpenExternalLinks(True)

        self.status_label = self.findChild(QLabel, 'statusLabel')
        self.finish_style_box = self.findChild(QComboBox, 'finishStyleBox')

        self.albedo_group = self.findChild(QGroupBox, 'albedoGroup')
        self.albedo_icon = self.findChild(QPushButton, 'albedoIcon')
        self.setalbedo_button = self.findChild(QToolButton, 'setalbedoButton')
        self.albedo_path_input = self.findChild(QLineEdit, 'albedoPathInput')

        self.is_compensating_box = self.findChild(QCheckBox, 'iscompensatingBox')
        self.compensation_coefficient_box = self.findChild(QDoubleSpinBox, 'coefficientBox')
        self.compensation_coefficient_label = self.findChild(QLabel, 'coefficientLabel')

        self.correct_button = self.findChild(QPushButton, 'correctButton')
        self.verify_button = self.findChild(QPushButton, 'verifyButton')

        self.metallic_group = self.findChild(QGroupBox, 'metallicGroup')
        self.metallic_icon = self.findChild(QPushButton, 'metallicIcon')
        self.setmetallic_button = self.findChild(QToolButton, 'setmetallicButton')
        self.metallic_path_input = self.findChild(QLineEdit, 'metallicPathInput')

        self.ao_group = self.findChild(QGroupBox, 'aoGroup')
        self.ao_icon = self.findChild(QPushButton, 'aoIcon')
        self.setao_button = self.findChild(QToolButton, 'setaoButton')
        self.ao_path_input = self.findChild(QLineEdit, 'aoPathInput')
        self.show_ao_box = self.findChild(QCheckBox, 'toggleaoBox')

        self.defaults_button = self.findChild(QPushButton, 'defaultsButton')
        self.save_button = self.findChild(QPushButton, 'saveButton')

        self.settings_group = self.findChild(QGroupBox, 'settingsGroup')
        self.luminance_label = self.findChild(QLabel, 'luminanceLabel')
        self.brightness_label = self.findChild(QLabel, 'brightnessLabel')
        self.l_min_box = self.findChild(QSpinBox, 'lminBox')
        self.l_max_box = self.findChild(QSpinBox, 'lmaxBox')
        self.b_limit_box = self.findChild(QSpinBox, 'blimitBox')

        self.info_link = self.findChild(QLabel, 'infoLink')
        self.info_link.setOpenExternalLinks(True)

        self.background = self.findChild(QWidget, 'background')
        self.background_layout = QVBoxLayout(self.background)
        self.background_layout.setContentsMargins(0, 0, 0, 0)
        self.background_image_label = QLabel()
        self.background_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.active_image_plane= self.findChild(QWidget, 'image_plane')
        self.active_image_layout = QVBoxLayout(self.active_image_plane)
        self.active_image_layout.setContentsMargins(0, 0, 0, 0)
        self.active_image_label = QLabel()
        self.active_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setalbedo_button.clicked.connect(lambda: self.load_texture(self.albedo_icon, self.albedo_path_input, True, image_type="albedo"))
        self.setmetallic_button.clicked.connect(lambda: self.load_texture(self.metallic_icon, self.metallic_path_input, image_type="metallic"))
        self.setao_button.clicked.connect(lambda: self.load_texture(self.ao_icon, self.ao_path_input, image_type="ao"))
        self.show_ao_box.clicked.connect(self.toggle_ao)
        self.correct_button.clicked.connect(self.correct_albedo)
        self.verify_button.clicked.connect(self.verify_albedo)
        self.save_button.clicked.connect(self.save_textures)
        self.finish_style_box.currentIndexChanged.connect(self.mode_changed)
        self.is_compensating_box.stateChanged.connect(self.compensating_state_changed)
        self.compensation_coefficient_box.valueChanged.connect(self.compensating_coeff_changed)
        self.exit_button.clicked.connect(self.exit_app)
        self.min_button.clicked.connect(self.min_app)
        self.l_min_box.valueChanged.connect(self.range_changed)
        self.l_max_box.valueChanged.connect(self.range_changed)
        self.b_limit_box.valueChanged.connect(self.range_changed)
        self.defaults_button.clicked.connect(self.write_cfg)

        self.is_compensating_box.setEnabled(self.is_compensating)
        self.compensation_coefficient_box.setValue(self.compensation_coefficient)
        self.l_min_box.setValue(self.l_min)
        self.l_max_box.setValue(self.l_max)
        self.b_limit_box.setValue(self.b_limit)
        self.finish_style_box.setCurrentText(self.finish_style)

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

    def load_texture(self, icon, texture_input, is_set_image=False, image_type="albedo"):
        texture_input.setStyleSheet("border-color: #343434;")
        try:
            filepath = QFileDialog.getOpenFileName(self, 'Open File', 'C:/', 'Image (*.tga;*.png;*.jpg;*.jpeg;*.jp2;*.bmp)')

            if filepath[0] != "":
                texture_input.setText(filepath[0])
                self.set_icon(Image.open(filepath[0]), icon)

            if is_set_image:
                self.active_image = Image.open(filepath[0]).convert("RGB")
                self.set_image(self.active_image_label, self.active_image_layout, 650, 650, Image.open(filepath[0]))

            if image_type == "ao":
                self.ao_image = Image.open(filepath[0]).convert("RGB")

            if image_type == "albedo":
                self.albedo_image = Image.open(filepath[0])

            if image_type == "metallic":
                self.metallic_image = Image.open(filepath[0])

            self.toggle_ao()

            self.status_label.setText("Albedo texture was loaded successfully")
        except Exception:
            pass

    def correct_albedo(self):
        self.albedo_path_input.setStyleSheet("border-color: #343434;")
        self.metallic_path_input.setStyleSheet("border-color: #343434;")

        valid_inputs = True
        if self.albedo_image is None:
            self.albedo_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if self.mode == "combined" and self.metallic_image is None:
            self.metallic_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if valid_inputs:
            self.central_widget.setEnabled(False)

            self.processing_thread.type = "correcting"
            self.processing_thread.albedo = self.albedo_image
            self.processing_thread.metallic = self.metallic_image
            self.processing_thread.mode = self.mode
            self.processing_thread.limit_values = [self.l_min, self.l_max, self.b_limit]
            self.processing_thread.is_compensating = self.is_compensating
            self.processing_thread.compensation_coefficient = self.compensation_coefficient
            self.processing_thread.start()

        else:
            self.status_label.setText("Please make sure you have attached valid textures")

    def verify_albedo(self):
        self.albedo_path_input.setStyleSheet("border-color: #343434;")
        self.metallic_path_input.setStyleSheet("border-color: #343434;")

        valid_inputs = True
        if self.albedo_image is None:
            self.albedo_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if self.mode == "combined" and self.metallic_image is None:
            self.metallic_path_input.setStyleSheet("border-color: #a03c3c;")
            valid_inputs = False

        if valid_inputs:
            self.central_widget.setEnabled(False)

            self.processing_thread.type = "verifying"
            self.processing_thread.albedo = self.albedo_image
            self.processing_thread.metallic = self.metallic_image
            self.processing_thread.mode = self.mode
            self.processing_thread.limit_values = [self.l_min, self.l_max, self.b_limit]
            self.processing_thread.start()

        else:
            self.status_label.setText("Please make sure you have attached valid textures")

    def save_textures(self):
        if self.pbr_set is not None:
            directory = os.path.dirname(self.albedo_path_input.text())
            filename = os.path.basename(self.albedo_path_input.text()).split(".")[0]
            try:
                selected_directory = QFileDialog.getExistingDirectory(self, "Select a directory", directory)
                self.pbr_set.save(selected_directory, filename)
                self.status_label.setText("Successfully saved")
            except Exception:
                self.status_label.setText("Saving interrupted by user")

        else:
            self.status_label.setText("Nothing to save")

    def compensating_state_changed(self):
        self.is_compensating = self.is_compensating_box.isChecked()
        self.compensation_coefficient_box.setEnabled(self.is_compensating)

    def compensating_coeff_changed(self):
        self.compensation_coefficient = self.compensation_coefficient_box.value()

    def mode_changed(self):
        self.finish_style = self.finish_style_box.currentText()

        if self.finish_style == "Gunsmith":
            self.mode = "combined"
            self.albedo_group.setEnabled(True)
            self.is_compensating_box.setEnabled(True)
            self.compensation_coefficient_box.setEnabled(self.is_compensating)
            self.metallic_group.setEnabled(True)
            self.luminance_label.setEnabled(True)
            self.brightness_label.setEnabled(True)
            self.l_min_box.setEnabled(True)
            self.l_max_box.setEnabled(True)
            self.b_limit_box.setEnabled(True)

        if self.finish_style in ["Patina", "Anodized Multicolored"]:
            self.mode = "metallic"
            self.albedo_group.setEnabled(True)
            self.is_compensating_box.setEnabled(True)
            self.compensation_coefficient_box.setEnabled(self.is_compensating)
            self.metallic_group.setEnabled(False)
            self.luminance_label.setEnabled(True)
            self.brightness_label.setEnabled(True)
            self.l_min_box.setEnabled(True)
            self.l_max_box.setEnabled(True)
            self.b_limit_box.setEnabled(True)

        if self.finish_style in ["Custom Paint Job", "Spray-Paint", "Hydrographic", "Anodized", "Anodized Airbrushed"]:
            self.mode = "nonmetallic"
            self.albedo_group.setEnabled(True)
            self.metallic_group.setEnabled(False)
            self.is_compensating_box.setEnabled(False)
            self.compensation_coefficient_box.setEnabled(False)
            self.luminance_label.setEnabled(True)
            self.brightness_label.setEnabled(False)
            self.l_min_box.setEnabled(True)
            self.l_max_box.setEnabled(True)
            self.b_limit_box.setEnabled(False)

    def range_changed(self):
        self.l_min = self.l_min_box.value()
        self.l_max = self.l_max_box.value()
        self.b_limit = self.b_limit_box.value()

    def toggle_ao(self):
        if self.show_ao_box.isChecked():
            if self.ao_image is None:
                self.ao_path_input.setStyleSheet("border-color: #a03c3c;")
                self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.active_image)

            elif self.active_image is not None:
                self.set_image(self.active_image_label, self.active_image_layout, 650, 650, ImageChops.multiply(self.active_image, self.ao_image.resize(self.active_image.size)))
            else:
                self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.ao_image)

        else:
            self.ao_path_input.setStyleSheet("border-color: #343434;")
            self.set_image(self.active_image_label, self.active_image_layout, 650, 650, self.active_image)

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

    @staticmethod
    def is_valid_image_path(image_path):
        try:
            with Image.open(image_path) as img:
                return True
        except (FileNotFoundError, IsADirectoryError):
            return False
        except:
            return False
