from UI.gui import GUI
from PyQt6.QtWidgets import QApplication
import sys
from Tools.CFG import CFG

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        cfg = CFG("Tools/config.cfg")
        window = GUI(cfg)
    except Exception:
        window = GUI()

    sys.exit(app.exec())
