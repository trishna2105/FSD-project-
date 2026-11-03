
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal


class SubjectsWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("UniPortal | My Subjects")
        self.resize(1100, 700)

        main = QVBoxLayout(self)
        main.setContentsMargins(65, 45, 65, 45)
        main.setSpacing(24)

        # Header
        header = QHBoxLayout()

        title = QLabel("My Subjects")
        title.setStyleSheet(
            "font-size: 32px; font-weight: 700;"
        )

        back_button = QPushButton("Back to Enrolment")
        back_button.setFixedWidth(190)
        back_button.clicked.connect(self.back_requested.emit)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_button)
        main.addLayout(header)

        # Description
        description = QLabel(
            "Your enrolled subjects and academic results."
        )
        description.setStyleSheet("color: #B4C3D5;")
        main.addWidget(description)

        # Summary cards
        summary = QHBoxLayout()
        summary.setSpacing(18)

        self.total_value = QLabel("0 / 4")
        self.average_value = QLabel("—")

        summary.addWidget(
            self.create_card("Total Subjects", self.total_value)
        )
        summary.addWidget(
            self.create_card("Average Mark", self.average_value)
        )

        main.addLayout(summary)

        # Subjects table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Subject ID", "Mark", "Grade"]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.table.verticalHeader().setVisible(False)

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #344256;
                alternate-background-color: #2C394D;
                border: none;
                border-radius: 14px;
                color: #F8FAFC;
                selection-background-color: #3469E8;
            }

            QHeaderView::section {
                background-color: #263448;
                color: #B4C3D5;
                padding: 14px;
                border: none;
                font-weight: 600;
            }

            QTableWidget::item {
                padding: 12px;
            }
        """)

        main.addWidget(self.table, 1)

    def create_card(self, label, value_widget):
        card = QFrame()
        card.setObjectName("summaryCard")

        card.setStyleSheet("""
            QFrame#summaryCard {
                background-color: #344256;
                border-radius: 15px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            "color: #B4C3D5; font-size: 13px;"
        )

        value_widget.setStyleSheet(
            "font-size: 28px; font-weight: 700;"
        )

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return card

    def update_subjects(self, subjects):
        """
        subjects example:
        [
            {"id": "101", "mark": 85, "grade": "HD"},
            {"id": "102", "mark": 78, "grade": "D"}
        ]
        """

        self.table.setRowCount(len(subjects))

        marks = []

        for row, subject in enumerate(subjects):
            subject_id = str(subject["id"])
            mark = subject["mark"]
            grade = str(subject["grade"])

            self.table.setItem(
                row, 0, QTableWidgetItem(subject_id)
            )
            self.table.setItem(
                row, 1, QTableWidgetItem(str(mark))
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(grade)
            )

            marks.append(float(mark))

        self.total_value.setText(
            f"{len(subjects)} / 4"
        )

        if marks:
            average = sum(marks) / len(marks)
            self.average_value.setText(
                f"{average:.1f}"
            )
        else:
            self.average_value.setText("—")
