
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal


class DashboardWindow(QWidget):
    enrolment_requested = Signal()
    subjects_requested = Signal()
    logout_requested = Signal()

    def __init__(self, student=None):
        super().__init__()
        self.student = student

        self.setWindowTitle("UniPortal | Dashboard")
        self.resize(1100, 700)

        main = QVBoxLayout(self)
        main.setContentsMargins(65, 45, 65, 45)
        main.setSpacing(25)

        # Header
        header = QHBoxLayout()

        brand = QLabel("Everything University.")
        brand.setStyleSheet(
            "font-size: 23px; font-weight: 700;"
        )

        logout = QPushButton("Log Out")
        logout.setFixedWidth(110)
        logout.clicked.connect(self.logout_requested.emit)

        header.addWidget(brand)
        header.addStretch()
        header.addWidget(logout)
        main.addLayout(header)

        # Welcome
        welcome = QLabel("Welcome back, Student.")
        welcome.setStyleSheet(
            "font-size: 32px; font-weight: 700;"
        )
        main.addWidget(welcome)

        subtitle = QLabel("Your academic overview")
        subtitle.setStyleSheet("color: #B4C3D5;")
        main.addWidget(subtitle)

        # Statistics
        grid = QGridLayout()
        grid.setSpacing(18)

        cards = [
            ("Enrolled Subjects", "0 / 4"),
            ("Average Mark", "—"),
            ("Academic Status", "Active"),
            ("Student ID", "—"),
        ]

        for index, (label, value) in enumerate(cards):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #344256;
                    border-radius: 15px;
                }
                QLabel {
                    background: transparent;
                }
            """)

            content = QVBoxLayout(card)
            content.setContentsMargins(22, 22, 22, 22)
            content.setSpacing(12)

            label_widget = QLabel(label)
            label_widget.setStyleSheet(
                "color: #B4C3D5; font-size: 13px;"
            )

            value_widget = QLabel(value)
            value_widget.setStyleSheet(
                "font-size: 26px; font-weight: 700;"
            )

            content.addWidget(label_widget)
            content.addWidget(value_widget)

            grid.addWidget(card, index // 2, index % 2)

        main.addLayout(grid)

        # Navigation buttons
        buttons = QHBoxLayout()
        buttons.setSpacing(16)

        enrolment = QPushButton("Enrolment")
        enrolment.clicked.connect(
            self.enrolment_requested.emit
        )

        subjects = QPushButton("My Subjects")
        subjects.clicked.connect(
            self.subjects_requested.emit
        )

        buttons.addWidget(enrolment)
        buttons.addWidget(subjects)
        main.addLayout(buttons)

        main.addStretch()
