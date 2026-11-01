import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uniapp.database import DEFAULT_DATA_PATH, Database
from uniapp.errors import (
    DataFormatError,
    DuplicateStudentError,
    StorageError,
    StudentNotFoundError,
)
from uniapp.models import Student, Subject


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "students.data"
        self.database = Database(self.path)
        self.database.ensure_exists()

    def make_student(self, student_id="000001", email="first@university.com"):
        return Student(student_id, "Demo Student", email, "Hello123", [Subject("007", 85, "HD")])

    def test_constructor_does_not_create_file(self):
        path = self.path.parent / "other.data"
        Database(path)
        self.assertFalse(path.exists())

    def test_initialization_creates_valid_empty_array(self):
        self.assertEqual(json.loads(self.path.read_text()), [])
        self.assertEqual(self.database.read_all(), [])

    def test_reinitialization_preserves_existing_bytes(self):
        self.path.write_text("not valid JSON", encoding="utf-8")
        before = self.path.read_bytes()
        self.database.ensure_exists()
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_parent_and_directory_path_raise_storage_error(self):
        for path in (self.path.parent / "missing" / "data", self.path.parent):
            with self.subTest(path=path), self.assertRaises(StorageError):
                Database(path).ensure_exists()

    def test_add_preserves_other_students_and_nested_subjects(self):
        first = self.make_student()
        second = self.make_student("000002", "second@university.com")
        self.database.add_student(first)
        self.database.add_student(second)
        restored = Database(self.path).read_all()
        self.assertEqual([student.to_dict() for student in restored], [first.to_dict(), second.to_dict()])
        self.assertIsInstance(restored[0].subjects[0], Subject)

    def test_read_in_another_process_preserves_id_and_mark(self):
        self.database.add_student(self.make_student())
        script = (
            "import sys; from uniapp.database import Database; "
            "s = Database(sys.argv[1]).read_all()[0]; "
            "print(s.student_id, s.subjects[0].subject_id, s.subjects[0].mark)"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(self.path)],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "000001 007 85")

    def test_search_normalizes_email_and_does_not_write(self):
        self.database.add_student(self.make_student())
        before = self.path.read_bytes()
        found = self.database.find_by_email(" FIRST@UNIVERSITY.COM ")
        self.assertEqual(found.student_id, "000001")
        self.assertEqual(self.database.find_by_id("000001").email, "first@university.com")
        self.assertIsNone(self.database.find_by_id("999999"))
        self.assertIsNone(self.database.find_by_email("missing@university.com"))
        self.assertEqual(self.path.read_bytes(), before)

    def test_duplicate_id_or_normalized_email_does_not_change_file(self):
        self.database.add_student(self.make_student())
        before = self.path.read_bytes()
        for student in (
            self.make_student("000001", "different@university.com"),
            self.make_student("000002", " FIRST@UNIVERSITY.COM "),
        ):
            with self.assertRaises(DuplicateStudentError):
                self.database.add_student(student)
            self.assertEqual(self.path.read_bytes(), before)

    def test_password_update_preserves_subjects_and_other_student(self):
        self.database.add_student(self.make_student())
        second = self.make_student("000002", "second@university.com")
        self.database.add_student(second)
        first = self.database.find_by_id("000001")
        first.password = "Newpass123"
        self.database.update_student(first)
        restored = self.database.read_all()
        self.assertEqual(restored[0].password, "Newpass123")
        self.assertEqual(restored[0].subjects[0].to_dict(), {"subject_id": "007", "mark": 85, "grade": "HD"})
        self.assertEqual(restored[1].to_dict(), second.to_dict())

    def test_editing_read_object_does_not_automatically_save(self):
        self.database.add_student(self.make_student())
        student = self.database.read_all()[0]
        student.password = "Newpass123"
        self.assertEqual(self.database.read_all()[0].password, "Hello123")

    def test_missing_update_does_not_insert(self):
        before = self.path.read_bytes()
        with self.assertRaises(StudentNotFoundError):
            self.database.update_student(self.make_student())
        self.assertEqual(self.path.read_bytes(), before)

    def test_update_cannot_take_another_students_email(self):
        self.database.add_student(self.make_student())
        self.database.add_student(self.make_student("000002", "second@university.com"))
        before = self.path.read_bytes()
        student = self.database.find_by_id("000001")
        student.email = "SECOND@UNIVERSITY.COM"
        with self.assertRaises(DuplicateStudentError):
            self.database.update_student(student)
        self.assertEqual(self.path.read_bytes(), before)

    def test_reusing_password_is_allowed(self):
        student = self.make_student()
        self.database.add_student(student)
        self.database.update_student(student)
        self.assertEqual(self.database.read_all()[0].password, "Hello123")

    def test_corrupt_data_is_not_overwritten_by_read_or_add(self):
        valid = self.make_student().to_dict()
        missing = dict(valid)
        del missing["subjects"]
        for text in (
            "", "   ", "not JSON", "{}", "null", "[null]",
            '[{"student_id":"000001","student_id":"000002"}]',
            json.dumps([missing]),
            json.dumps([valid, valid]),
        ):
            self.path.write_text(text, encoding="utf-8")
            before = self.path.read_bytes()
            with self.subTest(text=text):
                with self.assertRaises(DataFormatError):
                    self.database.read_all()
                with self.assertRaises(DataFormatError):
                    self.database.add_student(self.make_student("000003", "third@university.com"))
                self.assertEqual(self.path.read_bytes(), before)

    def test_duplicate_normalized_email_in_file_is_corruption(self):
        first = self.make_student().to_dict()
        second = self.make_student("000002", " FIRST@UNIVERSITY.COM ").to_dict()
        self.path.write_text(json.dumps([first, second]), encoding="utf-8")
        with self.assertRaises(DataFormatError):
            self.database.read_all()

    def test_invalid_credentials_are_rejected_on_read_and_write(self):
        for field, value in (("password", "Hell123"), ("email", "demo@other.com")):
            student = self.make_student()
            setattr(student, field, value)
            before = self.path.read_bytes()
            with self.assertRaises(DataFormatError):
                self.database.add_student(student)
            self.assertEqual(self.path.read_bytes(), before)
            self.path.write_text(json.dumps([student.to_dict()]), encoding="utf-8")
            with self.assertRaises(DataFormatError):
                self.database.read_all()
            self.path.write_text("[]", encoding="utf-8")

    def test_invalid_utf8_is_format_error(self):
        self.path.write_bytes(b"\xff\xfe")
        with self.assertRaises(DataFormatError):
            self.database.read_all()
        self.assertEqual(self.path.read_bytes(), b"\xff\xfe")

    def test_missing_file_is_not_recreated_by_read(self):
        self.path.unlink()
        with self.assertRaises(StorageError):
            self.database.read_all()
        self.assertFalse(self.path.exists())

    def test_read_permission_failure_is_not_reported_as_empty(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaises(StorageError):
                self.database.read_all()

    def test_replace_failure_preserves_original_and_cleans_temporary_file(self):
        self.database.add_student(self.make_student())
        before = self.path.read_bytes()
        with patch("uniapp.database.os.replace", side_effect=PermissionError("denied")):
            with self.assertRaises(StorageError):
                self.database.add_student(self.make_student("000002", "second@university.com"))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_temporary_file_creation_failure_preserves_original(self):
        before = self.path.read_bytes()
        with patch("uniapp.database.tempfile.NamedTemporaryFile", side_effect=OSError("disk full")):
            with self.assertRaises(StorageError):
                self.database.add_student(self.make_student())
        self.assertEqual(self.path.read_bytes(), before)

    def test_partial_write_failure_preserves_original_and_cleans_temporary_file(self):
        before = self.path.read_bytes()
        create_temporary_file = tempfile.NamedTemporaryFile

        def create_failing_file(*args, **kwargs):
            stream = create_temporary_file(*args, **kwargs)
            write = stream.write

            def fail_after_partial_write(text):
                write(text[:10])
                stream.flush()
                raise OSError("disk full")

            stream.write = fail_after_partial_write
            return stream

        with patch("uniapp.database.tempfile.NamedTemporaryFile", side_effect=create_failing_file):
            with self.assertRaises(StorageError):
                self.database.add_student(self.make_student())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_failed_password_update_keeps_stored_password(self):
        self.database.add_student(self.make_student())
        candidate = self.database.find_by_id("000001")
        candidate.password = "Newpass123"
        before = self.path.read_bytes()
        with patch("uniapp.database.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(StorageError):
                self.database.update_student(candidate)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.database.find_by_id("000001").password, "Hello123")

    def test_encoding_failure_preserves_original_and_cleans_temporary_file(self):
        before = self.path.read_bytes()
        student = self.make_student()
        student.name = "\ud800"
        with self.assertRaises(StorageError):
            self.database.add_student(student)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_default_path_is_project_relative_not_working_directory(self):
        expected = Path(__file__).resolve().parent.parent / "students.data"
        self.assertEqual(DEFAULT_DATA_PATH, expected)
        with patch("os.getcwd", return_value=self.temporary_directory.name):
            self.assertEqual(Database().path, expected)


if __name__ == "__main__":
    unittest.main()
