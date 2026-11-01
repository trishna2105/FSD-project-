import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Union

from uniapp.errors import (
    DataFormatError,
    DuplicateStudentError,
    StorageError,
    StudentNotFoundError,
    ValidationError,
)
from uniapp.models import Student
from uniapp.validation import (
    normalize_email,
    validate_email,
    validate_name,
    validate_password,
)


DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "students.data"


def _unique_json_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DataFormatError("JSON objects must not contain duplicate keys")
        result[key] = value
    return result


class Database:
    """JSON storage for one writer at a time; construction performs no file I/O."""

    def __init__(self, path: Union[str, Path] = DEFAULT_DATA_PATH) -> None:
        self.path = Path(path).absolute()

    def ensure_exists(self) -> None:
        try:
            # Exclusive creation avoids truncating an existing database.
            with self.path.open("x", encoding="utf-8") as stream:
                stream.write("[]\n")
        except FileExistsError as error:
            if not self.path.is_file():
                raise StorageError("Database path must be a file") from error
        except OSError as error:
            raise StorageError("Could not create the student data file") from error

    def read_all(self) -> list[Student]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except UnicodeError as error:
            raise DataFormatError("Student data must use UTF-8 encoding") from error
        except OSError as error:
            raise StorageError("Could not read the student data file") from error
        if not text.strip():
            raise DataFormatError("Student data file is empty; expected a JSON array")
        try:
            data = json.loads(text, object_pairs_hook=_unique_json_object)
        except json.JSONDecodeError as error:
            raise DataFormatError("Student data is not valid JSON") from error
        if not isinstance(data, list):
            raise DataFormatError("Student data must be a JSON array")
        students = [Student.from_dict(item) for item in data]
        self._validate_students(students)
        return students

    def find_by_id(self, student_id: str) -> Optional[Student]:
        for student in self.read_all():
            if student.student_id == student_id:
                return student
        return None

    def find_by_email(self, email: str) -> Optional[Student]:
        key = normalize_email(email)
        for student in self.read_all():
            if normalize_email(student.email) == key:
                return student
        return None

    def add_student(self, student: Student) -> None:
        self._validate_students([student])
        students = self.read_all()
        for existing in students:
            if (
                existing.student_id == student.student_id
                or normalize_email(existing.email) == normalize_email(student.email)
            ):
                raise DuplicateStudentError("Student ID or email already exists")
        students.append(student)
        self._write_all(students)

    def update_student(self, student: Student) -> None:
        """Replace one complete student; callers must include all existing subjects."""
        self._validate_students([student])
        students = self.read_all()
        index = None
        for position, existing in enumerate(students):
            if existing.student_id == student.student_id:
                index = position
        if index is None:
            raise StudentNotFoundError("Student ID does not exist")
        for existing in students:
            if (
                existing.student_id != student.student_id
                and normalize_email(existing.email) == normalize_email(student.email)
            ):
                raise DuplicateStudentError("Student email already exists")
        students[index] = student
        self._write_all(students)

    def delete_student(self, student_id: str) -> None:
        students = self.read_all()
        for position, student in enumerate(students):
            if student.student_id == student_id:
                del students[position]
                self._write_all(students)
                return
        raise StudentNotFoundError("Student ID does not exist")

    def clear(self) -> None:
        """Call only after UI confirmation; do not use to repair corrupt data."""
        self.read_all()
        self._write_all([])

    def _validate_students(self, students: list[Student]) -> None:
        student_ids = set()
        emails = set()
        for student in students:
            if not isinstance(student, Student):
                raise DataFormatError("Database entries must be Student objects")
            student.validate()
            try:
                validate_name(student.name)
                validate_email(student.email)
                validate_password(student.password)
            except ValidationError as error:
                raise DataFormatError(f"Invalid stored {error.field}: {error.reason}") from error
            email = normalize_email(student.email)
            if student.student_id in student_ids or email in emails:
                raise DataFormatError("Stored student IDs and emails must be unique")
            student_ids.add(student.student_id)
            emails.add(email)

    def _write_all(self, students: list[Student]) -> None:
        self._validate_students(students)
        data = [student.to_dict() for student in students]
        text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        temporary_path = None
        try:
            # Close a complete file in the same folder before replacing the original.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                stream.write(text)
            os.replace(temporary_path, self.path)
        except (OSError, UnicodeError) as error:
            raise StorageError("Could not save the student data file") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    # Cleanup must not hide the original save error.
                    pass
