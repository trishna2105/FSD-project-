
import sys
from pathlib import Path
from gui.subjects import SubjectsWindow
from PySide6.QtWidgets import QApplication, QMessageBox

from gui.login import LoginWindow
from gui.enrolment import EnrolmentWindow

from uniapp.auth import AuthService
from uniapp.database import Database
from uniapp.errors import DataFormatError, StorageError


def main():
    app = QApplication(sys.argv)

    # Load GUI stylesheet
    style_path = Path(__file__).parent / "styles.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    # Connect to database
    database = Database()

    try:
        database.ensure_exists()
        database.read_all()
    except (DataFormatError, StorageError) as error:
        QMessageBox.critical(None, "Database Error", str(error))
        return 1

    auth_service = AuthService(database)

    # Create windows
    login_window = LoginWindow(auth_service)
    enrolment_window = EnrolmentWindow()
    subjects_window = SubjectsWindow()
    current_student_id = None

    # Handle successful login
    def open_enrolment(student_id):
        nonlocal current_student_id

        student = database.find_by_id(student_id)

        if student is None:
            QMessageBox.warning(
                login_window,
                "Login Error",
                "Student account could not be found."
            )
            return

        current_student_id = student_id

        enrolment_window.setWindowTitle(
            f"Everything University. | {student.name}"
        )

        enrolment_window.show()
        login_window.hide()

    # Handle back button
    def back_to_login():
        enrolment_window.hide()
        login_window.show()

    def open_subjects():
        if current_student_id is None:
            return

        try:
            student = database.find_by_id(current_student_id)
        except (DataFormatError, StorageError) as error:
            QMessageBox.warning(
                enrolment_window,
                "Database Error",
                str(error)
            )
            return

        if student is None:
            QMessageBox.warning(
                enrolment_window,
                "Error",
                "Student account could not be found."
            )
            return

        subjects = [
            {
                "id": subject.subject_id,
                "mark": subject.mark,
                "grade": subject.grade
            }
            for subject in student.subjects
        ]

        subjects_window.update_subjects(subjects)
        subjects_window.show()
        enrolment_window.hide()


    def back_to_enrolment():
        subjects_window.hide()
        enrolment_window.show()

    # Connect signals
    login_window.login_success.connect(open_enrolment)
    enrolment_window.back_requested.connect(back_to_login)
    subjects_window.back_requested.connect(back_to_enrolment)
    enrolment_window.subjects_requested.connect(open_subjects)

    # Start application
    login_window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
