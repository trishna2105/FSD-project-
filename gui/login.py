from uniapp.auth import AuthService
from uniapp.errors import AuthenticationError, ValidationError
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal


class LoginWindow(QWidget):
    login_success = Signal(str)

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service

        self.setWindowTitle("UniPortal | Login")
        self.resize(1100, 700)
        self.setMinimumSize(650, 500)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(18)

        # Main title
        title = QLabel("Everything University.")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        # Email input
        self.email = QLineEdit()
        self.email.setPlaceholderText("University Email")
        self.email.setFixedWidth(420)
        self.email.setMinimumHeight(54)

        # Password input
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setFixedWidth(420)
        self.password.setMinimumHeight(54)

        # Sign In button
        login_button = QPushButton("Sign In")
        login_button.setFixedWidth(420)
        login_button.setMinimumHeight(54)
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.clicked.connect(self.handle_login)

        # Add widgets
        layout.addStretch(2)
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addSpacing(35)
        layout.addWidget(self.email, alignment=Qt.AlignCenter)
        layout.addWidget(self.password, alignment=Qt.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(login_button, alignment=Qt.AlignCenter)
        layout.addStretch(3)

        # Press Enter to sign in
        self.email.returnPressed.connect(self.handle_login)
        self.password.returnPressed.connect(self.handle_login)

    def handle_login(self):
        email = self.email.text().strip()
        password = self.password.text()

        if not email or not password:
            QMessageBox.warning(
                self,
                "Login Error",
                "Please enter your email and password."
                )
            return

        try:
            student = self.auth_service.login(email, password)

        except (AuthenticationError, ValidationError) as error:
            QMessageBox.warning(
                self,
                "Login Failed",
                str(error)
                )
            return

        self.login_success.emit(student.student_id)
