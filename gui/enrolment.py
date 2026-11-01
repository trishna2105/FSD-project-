
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QFrame
)
from PySide6.QtCore import Qt, Signal


class EnrolmentWindow(QWidget):
    back_requested = Signal()
    enrolment_requested = Signal(str)
    subjects_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("UniPortal | Enrolment")
        self.resize(1100, 700)

        main = QVBoxLayout(self)
        main.setContentsMargins(65, 45, 65, 45)
        main.setSpacing(22)

        # Header
        header = QHBoxLayout()

        title = QLabel("Course Enrolment")
        title.setStyleSheet(
            "font-size: 32px; font-weight: 700;"
        )

        back_button = QPushButton("Log Out")
        back_button.setFixedWidth(190)
        back_button.clicked.connect(self.back_requested.emit)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_button)
        main.addLayout(header)

        # Description
        description = QLabel(
            "Manage your subjects for this semester."
        )
        description.setStyleSheet("color: #B4C3D5;")
        main.addWidget(description)

        # Enrolment status
        self.status = QLabel("Enrolled Subjects: 0 / 4")
        self.status.setStyleSheet(
            "font-size: 18px; font-weight: 600;"
        )
        main.addWidget(self.status)

        # Subject ID input
        input_row = QHBoxLayout()
        input_row.setSpacing(14)

        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText(
            "Enter 3-digit Subject ID"
        )
        self.subject_input.setMaxLength(3)

        add_button = QPushButton("Enrol Subject")
        add_button.setFixedWidth(180)
        add_button.clicked.connect(self.request_enrolment)

        input_row.addWidget(self.subject_input)
        input_row.addWidget(add_button)
        main.addLayout(input_row)

        # Enrolled subject list
        list_card = QFrame()
        list_card.setObjectName("enrolmentCard")
        list_card.setStyleSheet("""
            QFrame#enrolmentCard {
                background-color: #344256;
                border-radius: 16px;
            }
        """)

        card_layout = QVBoxLayout(list_card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)

        list_title = QLabel("My Enrolled Subjects")
        list_title.setObjectName("sectionTitle")
        list_title.setStyleSheet(
            "font-size: 20px; font-weight: 600;"
        )

        self.subject_list = QListWidget()
        self.subject_list.setStyleSheet("""
            QListWidget {
                background-color: #263448;
                border: 1px solid #526178;
                border-radius: 10px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px;
            }
        """)

        card_layout.addWidget(list_title)
        card_layout.addWidget(self.subject_list)
        main.addWidget(list_card, 1)

         # View My Subjects button
        subjects_button = QPushButton("View My Subjects")
        subjects_button.setFixedWidth(220)
        subjects_button.setMinimumHeight(48)
        subjects_button.setCursor(Qt.PointingHandCursor)
        subjects_button.clicked.connect(self.subjects_requested.emit)

        main.addWidget(
            subjects_button,
            alignment=Qt.AlignRight
        )

    def request_enrolment(self):
        subject_id = self.subject_input.text().strip()
        self.enrolment_requested.emit(subject_id)

    def update_subjects(self, subjects):
        self.subject_list.clear()

        for subject in subjects:
            self.subject_list.addItem(str(subject))

        self.status.setText(
            f"Enrolled Subjects: {len(subjects)} / 4"
        )
        self.subject_input.clear()
