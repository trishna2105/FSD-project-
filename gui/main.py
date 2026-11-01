
import sys
from pathlib import Path
from gui.dashboard import DashboardWindow
from PySide6.QtWidgets import QApplication
from gui.login import LoginWindow


def main():
    app = QApplication(sys.argv)

    style_path = Path(__file__).with_name("styles.qss")

    if style_path.exists():
        app.setStyleSheet(
            style_path.read_text(encoding="utf-8")
        )

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
