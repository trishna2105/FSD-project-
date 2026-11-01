from pathlib import Path
from typing import Callable, Optional, Union

from uniapp.auth import AuthService
from uniapp.database import DEFAULT_DATA_PATH, Database
from uniapp.errors import (
    AuthenticationError,
    DataFormatError,
    DuplicateStudentError,
    IDGenerationError,
    StorageError,
    ValidationError,
)
from uniapp.models import Student


def _show_data_error(error: Exception) -> None:
    if isinstance(error, DataFormatError):
        print("\tStudent data is invalid. The file has not been reset.")
    else:
        print("\tCould not access or save student data. Please try again.")


def register_student(auth: AuthService) -> None:
    print("\tStudent Sign Up (enter x to cancel)")
    while True:
        email = input("\tEmail: ")
        if email.strip() == "x":
            return
        password = input("\tPassword: ")
        if password == "x":
            return
        try:
            auth.check_registration(email, password)
        except ValidationError:
            print("\tIncorrect email or password format")
            continue
        except DuplicateStudentError:
            print("\tStudent already exists")
            return
        except (DataFormatError, StorageError) as error:
            _show_data_error(error)
            return
        break

    while True:
        name = input("\tName: ")
        if name.strip() == "x":
            return
        try:
            student = auth.register(name, email, password)
        except ValidationError as error:
            if error.field == "name":
                print("\tName must not be empty")
                continue
            print("\tIncorrect email or password format")
            return
        except DuplicateStudentError:
            print("\tStudent already exists")
            return
        except IDGenerationError:
            print("\tCould not generate a student ID. Please try registering again.")
            return
        except (DataFormatError, StorageError) as error:
            _show_data_error(error)
            return
        print(f"\tEnrolling Student {student.name}")
        return


def login_student(auth: AuthService) -> Optional[Student]:
    print("\tStudent Sign In (enter x to go back)")
    while True:
        email = input("\tEmail: ")
        if email.strip() == "x":
            return None
        password = input("\tPassword: ")
        if password == "x":
            return None
        try:
            student = auth.login(email, password)
        except ValidationError:
            print("\tIncorrect email or password format")
            continue
        except AuthenticationError:
            print("\tStudent does not exist")
            return None
        except (DataFormatError, StorageError) as error:
            _show_data_error(error)
            return None
        print(f"\tLogin successful: {student.name}")
        return student


def student_menu(
    auth: AuthService,
    enrolment_handler: Optional[Callable[[Student, Database], None]] = None,
) -> None:
    """The enrolment handler keeps the student until its menu returns."""
    while True:
        choice = input("\tStudent System (l: Login / r: Register / x: Back): ").strip()
        if choice == "r":
            register_student(auth)
        elif choice == "l":
            student = login_student(auth)
            if student is not None:
                if enrolment_handler is None:
                    print("\tSubject enrolment menu is not connected yet.")
                else:
                    try:
                        enrolment_handler(student, auth.database)
                    except (DataFormatError, StorageError) as error:
                        _show_data_error(error)
                # Do not retain a logged-in student after the course menu exits.
                student = None
        elif choice == "x":
            return
        else:
            print("\tInvalid option, please try again")


def university_menu(
    auth: AuthService,
    admin_handler: Optional[Callable[[Database], None]] = None,
    enrolment_handler: Optional[Callable[[Student, Database], None]] = None,
) -> None:
    """Connect admin(database) and enrolment(student, database) when available."""
    while True:
        choice = input("University System (A: Admin / S: Student / X: Exit): ").strip()
        if choice == "A":
            if admin_handler is None:
                print("\tAdmin menu is not connected yet.")
            else:
                try:
                    admin_handler(auth.database)
                except (DataFormatError, StorageError) as error:
                    _show_data_error(error)
        elif choice == "S":
            student_menu(auth, enrolment_handler)
        elif choice == "X":
            print("Exiting University System")
            return
        else:
            print("Invalid option, please try again")


def main(
    path: Union[str, Path] = DEFAULT_DATA_PATH,
    admin_handler: Optional[Callable[[Database], None]] = None,
    enrolment_handler: Optional[Callable[[Student, Database], None]] = None,
) -> int:
    try:
        database = Database(path)
        database.ensure_exists()
        database.read_all()
        auth = AuthService(database)
        university_menu(auth, admin_handler, enrolment_handler)
    except (DataFormatError, StorageError) as error:
        _show_data_error(error)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nExiting University System")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
