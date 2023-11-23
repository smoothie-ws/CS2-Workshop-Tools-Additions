import sys

from PyQt6.QtWidgets import QApplication

from subprojects.GUI import GUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUI((1024, 768), "CS2 WTA test", "data/icons/app_icon.ico")
    window.show()
    sys.exit(app.exec())
