"""Fleet Manager — автономное десктоп-приложение (EVE Online).

Справедливое распределение персонажей флота. Запуск:  python main.py
"""
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

import config
import ui.styles as styles


def main():
    config.load()

    app = QApplication(sys.argv)
    app.setApplicationName("Fleet Manager")
    app.setStyle("Fusion")
    app.setStyleSheet(styles.apply_theme(config.get("theme", "default")))
    app.setFont(QFont("Segoe UI", 10))

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
