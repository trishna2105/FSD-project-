import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from uniapp.admin import admin_menu, format_student
from uniapp.cli import main
from uniapp.database import Database
from uniapp.errors import StorageError
from uniapp.enrolment import SubjectController
from uniapp.models import Student, Subject

controller = SubjectController()


def make_student(student_id, name, email, marks):
    subjects = [
        Subject(f"{index + 1:03d}", mark, controller.calculate_grade(mark))
        for index, mark in enumerate(marks)
    ]
    return Student(student_id, name, email, "Hello123", subjects)


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "students.data"
        self.database = Database(self.path)
        self.database.ensure_exists()

    def run_admin(self, answers):
        output = io.StringIO()
        with patch("builtins.input", side_effect=answers) as read_input:
            with redirect_stdout(output):
                admin_menu(self.database)
        prompts = [call.args[0] for call in read_input.call_args_list]
        return output.getvalue(), prompts

    def add_samples(self):
        self.database.add_student(make_student("000123", "Alen Jones", "alen@university.com", [60, 67]))
        self.database.add_student(make_student("000456", "Bea Smith", "bea@university.com", [90, 80]))
        self.database.add_student(make_student("000789", "Cal Low", "cal@university.com", [30]))
        self.database.add_student(make_student("000999", "Dee Empty", "dee@university.com", []))

    def test_format_student_matches_sample(self):
        student = make_student("762740", "Alen Jones", "alen@university.com", [60, 67])
        self.assertEqual(format_student(student), "Alen Jones :: 762740 --> GRADE:  P - MARK: 63.50")

    def test_menu_prompt_invalid_and_exit(self):
        output, prompts = self.run_admin(["z", " X "])
        self.assertEqual(prompts, ["\tAdmin System (c/g/p/r/s/x): "] * 2)
        self.assertIn("\tInvalid option, please try again", output)

    def test_show_empty_and_populated(self):
        output, _ = self.run_admin(["s", "x"])
        self.assertIn("\tStudent List\n\t\t< Nothing to Display >", output)
        self.add_samples()
        output, _ = self.run_admin(["s", "x"])
        self.assertIn("\tAlen Jones :: 000123 --> Email: alen@university.com", output)
        self.assertIn("\tDee Empty :: 000999 --> Email: dee@university.com", output)

    def test_group_students(self):
        output, _ = self.run_admin(["g", "x"])
        self.assertIn("\t\t< Nothing to Display >", output)
        self.add_samples()
        output, _ = self.run_admin(["g", "x"])
        self.assertIn("\tZ  --> [Cal Low :: 000789 --> GRADE:  Z - MARK: 30.00, "
                      "Dee Empty :: 000999 --> GRADE:  Z - MARK: 0.00]", output)
        self.assertIn("\tP  --> [Alen Jones :: 000123 --> GRADE:  P - MARK: 63.50]", output)
        self.assertIn("\tHD --> [Bea Smith :: 000456 --> GRADE: HD - MARK: 85.00]", output)
        self.assertNotIn("\tC  -->", output)

    def test_partition_students(self):
        output, _ = self.run_admin(["p", "x"])
        self.assertIn("\tFAIL --> []\n\tPASS --> []", output)
        self.add_samples()
        output, _ = self.run_admin(["p", "x"])
        self.assertIn("\tFAIL --> [Cal Low :: 000789 --> GRADE:  Z - MARK: 30.00, "
                      "Dee Empty :: 000999 --> GRADE:  Z - MARK: 0.00]", output)
        self.assertIn("\tPASS --> [Alen Jones :: 000123 --> GRADE:  P - MARK: 63.50, "
                      "Bea Smith :: 000456 --> GRADE: HD - MARK: 85.00]", output)

    def test_remove_existing_student_saves_json(self):
        self.add_samples()
        output, prompts = self.run_admin(["r", "000456", "x"])
        self.assertIn("\tRemove by ID: ", prompts)
        self.assertIn("\tRemoving Student 000456 Account", output)
        self.assertIsNone(self.database.find_by_id("000456"))
        self.assertEqual(len(self.database.read_all()), 3)
        # Persisted as JSON, not pickle.
        self.assertEqual(len(json.loads(self.path.read_text(encoding="utf-8"))), 3)

    def test_remove_missing_or_invalid_id_changes_nothing(self):
        self.add_samples()
        output, _ = self.run_admin(["r", "555555", "r", "abc", "r", "", "x"])
        self.assertIn("\tStudent 555555 does not exist", output)
        self.assertIn("\tStudent abc does not exist", output)
        self.assertIn("\tStudent  does not exist", output)
        self.assertEqual(len(self.database.read_all()), 4)

    def test_clear_requires_confirmation(self):
        self.add_samples()
        for answer in ("n", "", "no", "maybe"):
            output, prompts = self.run_admin(["c", answer, "x"])
            self.assertIn("\tClearing students database", output)
            self.assertIn("\tAre you sure you want to clear the database (Y)ES/(N)O: ", prompts)
            self.assertNotIn("Students data cleared", output)
            self.assertEqual(len(self.database.read_all()), 4)

    def test_clear_after_confirmation(self):
        self.add_samples()
        output, _ = self.run_admin(["c", " Y ", "x"])
        self.assertIn("\tStudents data cleared", output)
        self.assertEqual(self.database.read_all(), [])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), [])

    def test_invalid_data_is_reported_and_preserved(self):
        self.path.write_text("not json", encoding="utf-8")
        output, _ = self.run_admin(["s", "g", "p", "r", "1", "c", "y", "x"])
        self.assertEqual(
            output.count("\tStudent data is invalid. The file has not been reset."), 5
        )
        self.assertNotIn("Students data cleared", output)
        self.assertNotIn("Removing Student", output)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "not json")

    def test_storage_error_does_not_report_success(self):
        self.add_samples()
        with patch.object(Database, "_write_all", side_effect=StorageError("x")):
            output, _ = self.run_admin(["r", "000123", "c", "y", "x"])
        self.assertEqual(
            output.count("\tCould not access or save student data. Please try again."), 2
        )
        self.assertNotIn("Removing Student", output)
        self.assertNotIn("Students data cleared", output)
        self.assertEqual(len(self.database.read_all()), 4)

    def test_connected_through_university_menu(self):
        self.add_samples()
        output = io.StringIO()
        with patch("builtins.input", side_effect=["A", "r", "000789", "x", "X"]):
            with redirect_stdout(output):
                code = main(self.path, admin_handler=admin_menu)
        self.assertEqual(code, 0)
        self.assertIn("\tRemoving Student 000789 Account", output.getvalue())
        self.assertNotIn("not connected", output.getvalue())
        self.assertIsNone(self.database.find_by_id("000789"))


if __name__ == "__main__":
    unittest.main()