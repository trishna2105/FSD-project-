import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uniapp.auth import AuthService
from uniapp.database import Database
from uniapp.errors import (
    AuthenticationError,
    DataFormatError,
    DuplicateStudentError,
    IDGenerationError,
    StorageError,
    ValidationError,
)
from uniapp.models import Subject


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "students.data"
        self.database = Database(self.path)
        self.database.ensure_exists()
        self.auth = AuthService(self.database)

    def register_student(self):
        return self.auth.register("Demo Student", "demo@university.com", "Hello123")

    def test_registration_normalizes_email_and_name_then_persists(self):
        with patch("uniapp.auth.random.randint", return_value=123):
            student = self.auth.register("  김학생  ", " Demo@UNIVERSITY.COM ", "Hello123")
        self.assertEqual(student.student_id, "000123")
        self.assertEqual(student.name, "김학생")
        self.assertEqual(student.email, "demo@university.com")
        self.assertEqual(student.password, "Hello123")
        self.assertEqual(student.subjects, [])
        self.assertEqual(self.database.read_all()[0].to_dict(), student.to_dict())

    def test_new_service_can_login_after_registration(self):
        student = self.register_student()
        restored = AuthService(Database(self.path)).login(" DEMO@UNIVERSITY.COM ", "Hello123")
        self.assertEqual(restored.to_dict(), student.to_dict())
        self.assertIsNot(restored, student)

    def test_login_from_another_process(self):
        student = self.register_student()
        script = (
            "import sys; from uniapp.auth import AuthService; "
            "from uniapp.database import Database; "
            "s = AuthService(Database(sys.argv[1])).login('demo@university.com', 'Hello123'); "
            "print(s.student_id)"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(self.path)],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), student.student_id)

    def test_registration_check_does_not_write_or_generate_id(self):
        before = self.path.read_bytes()
        with patch("uniapp.auth.random.randint") as generate:
            self.assertIsNone(self.auth.check_registration("demo@university.com", "Hello123"))
        generate.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)

    def test_duplicate_email_is_rejected_by_check_and_register(self):
        self.register_student()
        before = self.path.read_bytes()
        with self.assertRaises(DuplicateStudentError):
            self.auth.check_registration(" DEMO@UNIVERSITY.COM ", "Hello123")
        with self.assertRaises(DuplicateStudentError):
            self.auth.register("Other Student", " DEMO@UNIVERSITY.COM ", "Otherpass123")
        self.assertEqual(self.path.read_bytes(), before)

    def test_registration_rechecks_after_prior_successful_check(self):
        self.auth.check_registration("demo@university.com", "Hello123")
        self.register_student()
        with self.assertRaises(DuplicateStudentError):
            self.register_student()
        self.assertEqual(len(self.database.read_all()), 1)

    def test_registration_rejects_invalid_name_without_saving(self):
        for name in ("", "   ", None):
            before = self.path.read_bytes()
            with self.assertRaises(ValidationError) as error:
                self.auth.register(name, "demo@university.com", "Hello123")
            self.assertEqual(error.exception.field, "name")
            self.assertEqual(self.path.read_bytes(), before)

    def test_all_auth_entry_points_validate_credentials(self):
        for method in (
            self.auth.check_registration,
            self.auth.login,
            lambda email, password: self.auth.register("Demo Student", email, password),
        ):
            for email, password, field in (
                ("", "Hello123", "email"),
                (None, "Hello123", "email"),
                ("demo@other.com", "Hello123", "email"),
                ("demo@university.com", "", "password"),
                ("demo@university.com", None, "password"),
                ("demo@university.com", "Hell123", "password"),
            ):
                before = self.path.read_bytes()
                with self.assertRaises(ValidationError) as error:
                    method(email, password)
                self.assertEqual(error.exception.field, field)
                self.assertEqual(self.path.read_bytes(), before)

    def test_valid_but_mismatched_credentials_raise_authentication_error(self):
        self.register_student()
        before = self.path.read_bytes()
        for email, password in (
            ("missing@university.com", "Hello123"),
            ("demo@university.com", "Hello124"),
            ("demo@university.com", "HELLO123"),
        ):
            with self.assertRaises(AuthenticationError) as error:
                self.auth.login(email, password)
            self.assertNotIn(password, str(error.exception))
        self.assertEqual(self.path.read_bytes(), before)

    def test_password_whitespace_is_not_removed(self):
        self.register_student()
        for password in (" Hello123", "Hello123 ", "Hello123\n"):
            with self.assertRaises(ValidationError):
                self.auth.login("demo@university.com", password)

    def test_id_collision_retries_and_preserves_existing_student(self):
        with patch("uniapp.auth.random.randint", return_value=1):
            first = self.register_student()
        with patch("uniapp.auth.random.randint", side_effect=[1, 1, 2]) as generate:
            second = self.auth.register("Second", "second@university.com", "Hello123")
        self.assertEqual(generate.call_count, 3)
        self.assertEqual(second.student_id, "000002")
        self.assertEqual(self.database.find_by_id(first.student_id).to_dict(), first.to_dict())
        self.assertEqual(len(self.database.read_all()), 2)

    def test_id_generation_limit_raises_without_saving(self):
        with patch("uniapp.auth.random.randint", return_value=1):
            self.register_student()
        before = self.path.read_bytes()
        with patch("uniapp.auth.MAX_ID_ATTEMPTS", 3):
            with patch("uniapp.auth.random.randint", return_value=1) as generate:
                with self.assertRaises(IDGenerationError):
                    self.auth.register("Second", "second@university.com", "Hello123")
        self.assertEqual(generate.call_count, 3)
        self.assertEqual(self.path.read_bytes(), before)

    def test_generated_id_boundaries(self):
        for number, expected in ((1, "000001"), (999999, "999999")):
            with patch("uniapp.auth.random.randint", return_value=number):
                student = self.auth.register("Demo Student", f"demo{number}@university.com", "Hello123")
            self.assertEqual(student.student_id, expected)

    def test_login_reads_current_password_and_subjects(self):
        student = self.register_student()
        student.password = "Newpass123"
        student.subjects.append(Subject("007", 85, "HD"))
        Database(self.path).update_student(student)
        with self.assertRaises(AuthenticationError):
            self.auth.login("demo@university.com", "Hello123")
        before = self.path.read_bytes()
        restored = self.auth.login("demo@university.com", "Newpass123")
        self.assertEqual(restored.subjects[0].to_dict(), student.subjects[0].to_dict())
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_file_is_storage_error_for_all_entry_points(self):
        self.path.unlink()
        with self.assertRaises(StorageError):
            self.auth.login("demo@university.com", "Hello123")
        with self.assertRaises(StorageError):
            self.auth.check_registration("demo@university.com", "Hello123")
        with self.assertRaises(StorageError):
            self.register_student()
        self.assertFalse(self.path.exists())

    def test_corrupt_file_is_not_treated_as_authentication_failure(self):
        self.path.write_text("not JSON", encoding="utf-8")
        before = self.path.read_bytes()
        with self.assertRaises(DataFormatError):
            self.auth.login("demo@university.com", "Hello123")
        with self.assertRaises(DataFormatError):
            self.register_student()
        self.assertEqual(self.path.read_bytes(), before)

    def test_registration_does_not_return_success_when_save_fails(self):
        before = self.path.read_bytes()
        with patch("uniapp.database.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(StorageError):
                self.register_student()
        self.assertEqual(self.path.read_bytes(), before)

    def test_database_final_duplicate_check_is_not_suppressed(self):
        with patch.object(self.database, "add_student", side_effect=DuplicateStudentError("duplicate")):
            with self.assertRaises(DuplicateStudentError):
                self.register_student()
        self.assertEqual(self.database.read_all(), [])

    def test_import_has_no_output_and_does_not_create_database(self):
        project = Path(__file__).resolve().parent.parent
        script = (
            "import sys; from unittest.mock import patch; sys.path.insert(0, sys.argv[1]); "
            "guard = patch('pathlib.Path.open', side_effect=AssertionError('unexpected file I/O')); "
            "guard.start(); import uniapp.auth; guard.stop()"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(project)],
            cwd=self.temporary_directory.name,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(sorted(path.name for path in self.path.parent.iterdir()), ["students.data"])


if __name__ == "__main__":
    unittest.main()
