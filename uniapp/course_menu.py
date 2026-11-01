from uniapp.enrolment import SubjectController
from uniapp.models import Student
from uniapp.validation import validate_password
from uniapp.errors import ValidationError, DataFormatError, StorageError

def course_menu(student, database):
    controller = SubjectController()

    while True:
        choice = input(
            "\nStudent Course Menu "
            "(c: Change Password / e: Enrol Subject / "
            "r: Remove Subject / s: Show Subjects / x: Exit): "
        ).strip().lower()

        if choice == "e":
            student = controller.enrol_subject(student, database)

        elif choice == "r":
            subject_id = input("\tRemove Subject by ID: ").strip()

            student = controller.remove_subject(
                student, database, subject_id
            )
        elif choice == "c":
            print("Updating Password")

            current_password = input("Current Password: ")

            if current_password != student.password:
                print("Current password is incorrect")
                continue

            new_password = input("New Password: ")
            confirm_password = input("Confirm Password: ")

            if new_password != confirm_password:
                print("Passwords do not match - try again")
                continue

            try:
                validate_password(new_password)

                candidate = Student.from_dict(student.to_dict())
                candidate.password = new_password

                database.update_student(candidate)

            except ValidationError:
                print("Incorrect password format")

            except (DataFormatError, StorageError):
                print("Could not save password. Please try again.")

            else:
                student = candidate
                print("Password updated successfully")

        elif choice == "s":
            controller.show_subjects(student)

        elif choice == "x":
            return

        else:
            print("Invalid option, please try again")