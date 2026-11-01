import random

from uniapp.database import Database
from uniapp.errors import AuthenticationError, DuplicateStudentError, IDGenerationError
from uniapp.models import Student
from uniapp.validation import (
    normalize_email,
    validate_email,
    validate_name,
    validate_password,
)


MAX_ID_ATTEMPTS = 1000


class AuthService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def _validate_credentials(self, email: str, password: str) -> str:
        email = normalize_email(email)
        validate_email(email)
        validate_password(password)
        return email

    def check_registration(self, email: str, password: str) -> None:
        """Check before the UI asks for a name; this does not reserve an account."""
        email = self._validate_credentials(email, password)
        if self.database.find_by_email(email) is not None:
            raise DuplicateStudentError("Student email already exists")

    def register(self, name: str, email: str, password: str) -> Student:
        # Repeat the checks even if the UI already called check_registration().
        self.check_registration(email, password)
        validate_name(name)
        email = normalize_email(email)
        existing_ids = {student.student_id for student in self.database.read_all()}
        student_id = self._generate_student_id(existing_ids)
        student = Student(student_id, name.strip(), email, password)
        self.database.add_student(student)
        return student

    def login(self, email: str, password: str) -> Student:
        email = self._validate_credentials(email, password)
        student = self.database.find_by_email(email)
        if student is None or student.password != password:
            raise AuthenticationError("Student email or password does not match")
        return student

    def _generate_student_id(self, existing_ids: set[str]) -> str:
        for _ in range(MAX_ID_ATTEMPTS):
            candidate = f"{random.randint(1, 999999):06d}"
            if candidate not in existing_ids:
                return candidate
        raise IDGenerationError("Could not generate an unused student ID; try again")
