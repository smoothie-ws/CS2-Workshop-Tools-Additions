from UI.gui import GUI
from PyQt6.QtWidgets import QApplication
import sys
from Tools.CFG import CFG


app = QApplication(sys.argv)

try:
    cfg = CFG("config.cfg")
    window = GUI(cfg)
    print(cfg.version)
except Exception:
    window = GUI()

sys.exit(app.exec())
