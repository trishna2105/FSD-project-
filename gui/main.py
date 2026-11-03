
import sys
from pathlib import Path
from gui.subjects import SubjectsWindow
from PySide6.QtWidgets import QApplication, QMessageBox
from uniapp.enrolment import SubjectController
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
    subject_controller = SubjectController()

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
        enrolment_window.update_subjects([
            f"Subject {subject.subject_id}"
            for subject in student.subjects
        ])

        enrolment_window.setWindowTitle(
            f"Everything University. | {student.name}"
        )

        enrolment_window.show()
        login_window.hide()

    # Handle back button
    def back_to_login():
        enrolment_window.hide()
        login_window.show()

    def enrol_subject():
        if current_student_id is None:
            return

        try:
            student = database.find_by_id(current_student_id)

            if student is None:
                QMessageBox.warning(
                    enrolment_window,
                    "Error",
                    "Student account could not be found."
                )
                return

            if len(student.subjects) >= 4:
                QMessageBox.warning(
                    enrolment_window,
                    "Enrolment Limit",
                    "You can only enrol in a maximum of 4 subjects."
                )
                return

            updated_student = subject_controller.enrol_subject(
                student, database
            )

            enrolment_window.update_subjects([
                f"Subject {subject.subject_id}"
                for subject in updated_student.subjects
            ])

            QMessageBox.information(
                enrolment_window,
                "Enrolment Successful",
                "You have successfully enrolled in a subject."
            )

        except Exception as error:
            QMessageBox.warning(
                enrolment_window,
                "Enrolment Error",
                str(error)
            )

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
    def drop_subject(subject_id):
        if current_student_id is None:
            return

        if not (len(subject_id) == 3 and subject_id.isdigit()):
            QMessageBox.warning(
                enrolment_window,
                "Invalid Subject ID",
                "Please enter a valid 3-digit Subject ID."
            )
            return

        try:
            student = database.find_by_id(current_student_id)

            if student is None:
                QMessageBox.warning(
                    enrolment_window,
                    "Error",
                    "Student account could not be found."
                )
                return

            if not any(
                subject.subject_id == subject_id
                for subject in student.subjects
            ):
                QMessageBox.warning(
                    enrolment_window,
                    "Subject Not Found",
                    "You are not enrolled in this subject."
                )
                return

            updated_student = subject_controller.remove_subject(
                student, database, subject_id
            )

            enrolment_window.update_subjects([
                f"Subject {subject.subject_id}"
                for subject in updated_student.subjects
            ])

            QMessageBox.information(
                enrolment_window,
                "Subject Dropped",
                f"Subject {subject_id} has been removed."
            )

        except Exception as error:
            QMessageBox.warning(
                enrolment_window,
                "Drop Error",
                str(error)
            )

    def back_to_enrolment():
        subjects_window.hide()
        enrolment_window.show()

    # Connect signals
    login_window.login_success.connect(open_enrolment)
    enrolment_window.back_requested.connect(back_to_login)
    subjects_window.back_requested.connect(back_to_enrolment)
    enrolment_window.subjects_requested.connect(open_subjects)
    enrolment_window.enrolment_requested.connect(
        lambda _subject_id: enrol_subject()
    )
    enrolment_window.drop_requested.connect(drop_subject)

    # Start application
    login_window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
