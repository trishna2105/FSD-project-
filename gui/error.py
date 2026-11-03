
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt


class ErrorDialog(QDialog):
    def __init__(
        self,
        parent=None,
        title="Something went wrong",
        message="An unexpected error occurred."
    ):
        super().__init__(parent)

        self.setWindowTitle("UniPortal | Error")
        self.setModal(True)
        self.setFixedSize(440, 280)
        self.setObjectName("errorDialog")

        main = QVBoxLayout(self)
        main.setContentsMargins(30, 30, 30, 30)
        main.setSpacing(18)

        # Error icon
        icon = QLabel("!")
        icon.setObjectName("errorIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(46, 46)

        # Error title
        title_label = QLabel(title)
        title_label.setObjectName("errorTitle")
        title_label.setWordWrap(True)

        # Error message
        message_label = QLabel(message)
        message_label.setObjectName("errorMessage")
        message_label.setWordWrap(True)

        # Header
        header = QHBoxLayout()
        header.setSpacing(14)
        header.addWidget(icon)
        header.addWidget(title_label, 1)

        main.addLayout(header)
        main.addWidget(message_label)
        main.addStretch()

        # Close button
        button_row = QHBoxLayout()
        button_row.addStretch()

        close_button = QPushButton("Got it")
        close_button.setFixedWidth(130)
        close_button.clicked.connect(self.accept)

        button_row.addWidget(close_button)
        main.addLayout(button_row)


def show_error(parent, title, message):
    dialog = ErrorDialog(
        parent=parent,
        title=title,
        message=message
    )
    return dialog.exec()
