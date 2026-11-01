from __future__ import annotations

import re
from typing import Any, Optional

from uniapp.errors import DataFormatError


def _validate_id(value: str, digits: int, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or re.fullmatch(rf"[0-9]{{{digits}}}", value) is None
        or int(value) == 0
    ):
        raise DataFormatError(f"{field_name} must be a nonzero {digits}-digit string")


def _validate_fields(data: object, expected: set[str], model: str) -> None:
    if not isinstance(data, dict) or set(data) != expected:
        # Do not include incoming keys or values: they may contain credentials.
        raise DataFormatError(f"{model} must contain exactly the required fields")


class Subject:
    """Shared subject data; enrolment owns generation and grade calculation."""

    def __init__(self, subject_id: str, mark: int, grade: str) -> None:
        self.subject_id = subject_id
        self.mark = mark
        self.grade = grade
        self.validate()

    def validate(self) -> None:
        _validate_id(self.subject_id, 3, "subject_id")
        if type(self.mark) is not int or not 25 <= self.mark <= 100:
            raise DataFormatError("mark must be an integer between 25 and 100")
        if not isinstance(self.grade, str) or self.grade not in ("Z", "P", "C", "D", "HD"):
            raise DataFormatError("grade must be Z, P, C, D or HD")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "subject_id": self.subject_id,
            "mark": self.mark,
            "grade": self.grade,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Subject:
        _validate_fields(data, {"subject_id", "mark", "grade"}, "Subject")
        return cls(data["subject_id"], data["mark"], data["grade"])


class Student:
    def __init__(
        self,
        student_id: str,
        name: str,
        email: str,
        password: str,
        subjects: Optional[list[Subject]] = None,
    ) -> None:
        self.student_id = student_id
        self.name = name
        self.email = email
        self.password = password
        if subjects is None:
            self.subjects = []
        else:
            self.subjects = subjects
        self.validate()

    def validate(self) -> None:
        _validate_id(self.student_id, 6, "student_id")
        for field_name in ("name", "email", "password"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise DataFormatError(f"{field_name} must be a nonempty string")
        if not isinstance(self.subjects, list) or len(self.subjects) > 4:
            raise DataFormatError("subjects must be a list of at most four subjects")
        seen_ids = set()
        for subject in self.subjects:
            if not isinstance(subject, Subject):
                raise DataFormatError("subjects must contain Subject objects")
            subject.validate()
            if subject.subject_id in seen_ids:
                raise DataFormatError("subject_id must be unique within a student")
            seen_ids.add(subject.subject_id)

    def to_dict(self) -> dict[str, Any]:
        """Return storage data, including the password; never use it for logging."""
        self.validate()
        return {
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "subjects": [subject.to_dict() for subject in self.subjects],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Student:
        _validate_fields(
            data,
            {"student_id", "name", "email", "password", "subjects"},
            "Student",
        )
        if not isinstance(data["subjects"], list):
            raise DataFormatError("subjects must be a list")
        return cls(
            student_id=data["student_id"],
            name=data["name"],
            email=data["email"],
            password=data["password"],
            subjects=[Subject.from_dict(subject) for subject in data["subjects"]],
        )
