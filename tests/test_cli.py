import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from uniapp.auth import AuthService
from uniapp.cli import main
from uniapp.database import Database
from uniapp.errors import StorageError


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "students.data"
        self.database = Database(self.path)
        self.database.ensure_exists()

    def run_cli(self, answers, **handlers):
        output = io.StringIO()
        with patch("builtins.input", side_effect=answers) as read_input:
            with redirect_stdout(output):
                code = main(self.path, **handlers)
        prompts = [call.args[0] for call in read_input.call_args_list]
        return code, output.getvalue(), prompts

    def register_existing(self):
        return AuthService(self.database).register("Demo Student", "demo@university.com", "Hello123")

    def test_startup_creates_missing_database_and_exit(self):
        self.path.unlink()
        code, output, prompts = self.run_cli(["X"])
        self.assertEqual(code, 0)
        self.assertEqual(self.database.read_all(), [])
        self.assertEqual(prompts, ["University System (A: Admin / S: Student / X: Exit): "])
        self.assertIn("Exiting University System", output)

    def test_register_login_and_pass_student_to_enrolment(self):
        enrolment = Mock()
        code, output, prompts = self.run_cli(
            ["S", "r", " Demo@UNIVERSITY.COM ", "Hello123", " Demo Student ",
             "l", "demo@university.com", "Hello123", "x", "X"],
            enrolment_handler=enrolment,
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(self.database.read_all()), 1)
        self.assertIn("Enrolling Student Demo Student", output)
        self.assertIn("Login successful: Demo Student", output)
        enrolment.assert_called_once()
        student, database = enrolment.call_args.args
        self.assertEqual(student.email, "demo@university.com")
        self.assertEqual(database.path, self.path)
        self.assertLess(prompts.index("\tPassword: "), prompts.index("\tName: "))

    def test_registration_does_not_automatically_login(self):
        enrolment = Mock()
        _, output, _ = self.run_cli(
            ["S", "r", "demo@university.com", "Hello123", "Demo", "x", "X"],
            enrolment_handler=enrolment,
        )
        enrolment.assert_not_called()
        self.assertNotIn("Login successful", output)

    def test_registration_format_failure_retries_credentials(self):
        _, output, prompts = self.run_cli(
            ["S", "r", "demo@other.com", "Hello123", "demo@university.com",
             "Hello123", "Demo", "x", "X"]
        )
        self.assertIn("Incorrect email or password format", output)
        self.assertEqual(prompts.count("\tEmail: "), 2)
        self.assertEqual(prompts.count("\tName: "), 1)
        self.assertEqual(len(self.database.read_all()), 1)

    def test_duplicate_registration_returns_without_asking_for_name(self):
        self.register_existing()
        before = self.path.read_bytes()
        _, output, prompts = self.run_cli(
            ["S", "r", "DEMO@UNIVERSITY.COM", "Hello123", "x", "X"]
        )
        self.assertIn("Student already exists", output)
        self.assertNotIn("\tName: ", prompts)
        self.assertEqual(self.path.read_bytes(), before)

    def test_empty_name_retries_name(self):
        _, output, prompts = self.run_cli(
            ["S", "r", "demo@university.com", "Hello123", "   ", "Demo", "x", "X"]
        )
        self.assertIn("Name must not be empty", output)
        self.assertEqual(prompts.count("\tEmail: "), 1)
        self.assertEqual(prompts.count("\tName: "), 2)
        self.assertEqual(self.database.read_all()[0].name, "Demo")

    def test_registration_can_cancel_at_each_input_without_saving(self):
        for answers, password_count, name_count in (
            (["S", "r", "x", "x", "X"], 0, 0),
            (["S", "r", "demo@university.com", "x", "x", "X"], 1, 0),
            (["S", "r", "demo@university.com", "Hello123", "x", "x", "X"], 1, 1),
        ):
            before = self.path.read_bytes()
            with patch.object(AuthService, "register") as register:
                code, output, prompts = self.run_cli(answers)
            self.assertEqual(code, 0)
            register.assert_not_called()
            self.assertIn("enter x to cancel", output)
            self.assertNotIn("Enrolling Student", output)
            self.assertEqual(prompts.count("\tPassword: "), password_count)
            self.assertEqual(prompts.count("\tName: "), name_count)
            self.assertEqual(self.path.read_bytes(), before)

    def test_registration_can_cancel_after_invalid_credentials_or_name(self):
        for answers in (
            ["S", "r", "demo@gmail.com", "Hello123", "x", "x", "X"],
            ["S", "r", "demo@university.com", "Hello123", "   ", "x", "x", "X"],
        ):
            before = self.path.read_bytes()
            _, output, _ = self.run_cli(answers)
            self.assertNotIn("Enrolling Student", output)
            self.assertEqual(self.path.read_bytes(), before)

    def test_failed_save_does_not_print_registration_success(self):
        before = self.path.read_bytes()
        with patch("uniapp.database.os.replace", side_effect=OSError("disk error")):
            _, output, _ = self.run_cli(
                ["S", "r", "demo@university.com", "Hello123", "Demo", "x", "X"]
            )
        self.assertIn("Could not access or save student data", output)
        self.assertNotIn("Enrolling Student", output)
        self.assertEqual(self.path.read_bytes(), before)

    def test_id_generation_failure_returns_without_saving(self):
        before = self.path.read_bytes()
        with patch("uniapp.auth.MAX_ID_ATTEMPTS", 0):
            _, output, _ = self.run_cli(
                ["S", "r", "demo@university.com", "Hello123", "Demo", "x", "X"]
            )
        self.assertIn("Could not generate a student ID", output)
        self.assertNotIn("Enrolling Student", output)
        self.assertEqual(self.path.read_bytes(), before)

    def test_login_format_failure_retries_in_same_flow(self):
        self.register_existing()
        enrolment = Mock()
        _, output, prompts = self.run_cli(
            ["S", "l", "demo@university.com", "Hell123", "demo@university.com",
             "Hello123", "x", "X"], enrolment_handler=enrolment,
        )
        self.assertIn("Incorrect email or password format", output)
        self.assertEqual(prompts.count("\tEmail: "), 2)
        enrolment.assert_called_once()

    def test_login_can_go_back_from_email_prompt(self):
        before = self.path.read_bytes()
        enrolment = Mock()
        _, output, prompts = self.run_cli(
            ["S", "l", "x", "x", "X"], enrolment_handler=enrolment,
        )
        self.assertIn("enter x to go back", output)
        self.assertNotIn("\tPassword: ", prompts)
        self.assertNotIn("Incorrect email or password format", output)
        self.assertNotIn("Login successful", output)
        self.assertEqual(prompts.count("\tStudent System (l: Login / r: Register / x: Back): "), 2)
        self.assertEqual(self.path.read_bytes(), before)
        enrolment.assert_not_called()

    def test_login_can_go_back_from_password_prompt(self):
        enrolment = Mock()
        with patch.object(AuthService, "login") as authenticate:
            _, output, _ = self.run_cli(
                ["S", "l", "demo@university.com", "x", "x", "X"],
                enrolment_handler=enrolment,
            )
        authenticate.assert_not_called()
        enrolment.assert_not_called()
        self.assertNotIn("Incorrect email or password format", output)
        self.assertNotIn("Login successful", output)

    def test_login_can_go_back_after_format_error(self):
        _, output, prompts = self.run_cli(
            ["S", "l", "demo@university.com", "Hell123", "x", "x", "X"]
        )
        self.assertEqual(output.count("Incorrect email or password format"), 1)
        self.assertEqual(prompts.count("\tEmail: "), 2)
        self.assertEqual(prompts.count("\tPassword: "), 1)

    def test_authentication_failure_returns_to_student_menu(self):
        self.register_existing()
        enrolment = Mock()
        _, output, prompts = self.run_cli(
            ["S", "l", "demo@university.com", "Wrongpass123", "x", "X"],
            enrolment_handler=enrolment,
        )
        self.assertIn("Student does not exist", output)
        self.assertEqual(prompts.count("\tEmail: "), 1)
        self.assertEqual(prompts.count("\tStudent System (l: Login / r: Register / x: Back): "), 2)
        enrolment.assert_not_called()

    def test_storage_failure_is_not_reported_as_authentication_failure(self):
        with patch.object(AuthService, "login", side_effect=StorageError("read failed")):
            _, output, _ = self.run_cli(
                ["S", "l", "demo@university.com", "Hello123", "x", "X"]
            )
        self.assertIn("Could not access or save student data", output)
        self.assertNotIn("Student does not exist", output)

    def test_admin_gets_database_without_student_login(self):
        admin = Mock()
        _, _, prompts = self.run_cli(["A", "X"], admin_handler=admin)
        admin.assert_called_once()
        self.assertEqual(admin.call_args.args[0].path, self.path)
        self.assertNotIn("\tEmail: ", prompts)

    def test_missing_team_menus_are_explicit(self):
        self.register_existing()
        _, output, _ = self.run_cli(
            ["A", "S", "l", "demo@university.com", "Hello123", "x", "X"]
        )
        self.assertIn("Admin menu is not connected yet", output)
        self.assertIn("Subject enrolment menu is not connected yet", output)

    def test_invalid_commands_retry_and_command_whitespace_is_trimmed(self):
        _, output, prompts = self.run_cli(["", "a", " S ", "L", "", " x ", " X "])
        self.assertEqual(output.count("Invalid option"), 4)
        self.assertEqual(prompts.count("University System (A: Admin / S: Student / X: Exit): "), 4)
        self.assertEqual(prompts.count("\tStudent System (l: Login / r: Register / x: Back): "), 3)

    def test_repeated_menu_visits_do_not_use_recursive_calls(self):
        answers = [answer for _ in range(1100) for answer in ("S", "x")]
        answers.append("X")
        code, _, _ = self.run_cli(answers)
        self.assertEqual(code, 0)

    def test_returning_from_course_menu_requires_login_for_next_visit(self):
        self.register_existing()
        enrolment = Mock()
        _, _, prompts = self.run_cli(
            ["S", "l", "demo@university.com", "Hello123", "x",
             "S", "l", "demo@university.com", "Hello123", "x", "X"],
            enrolment_handler=enrolment,
        )
        self.assertEqual(enrolment.call_count, 2)
        self.assertEqual(prompts.count("\tEmail: "), 2)

    def test_team_handler_storage_error_returns_to_parent_menu(self):
        admin = Mock(side_effect=StorageError("failed"))
        _, output, _ = self.run_cli(["A", "X"], admin_handler=admin)
        self.assertIn("Could not access or save student data", output)

    def test_corrupt_startup_file_is_preserved_and_menu_is_not_opened(self):
        self.path.write_text("not JSON", encoding="utf-8")
        code, output, prompts = self.run_cli([])
        self.assertEqual(code, 1)
        self.assertIn("Student data is invalid", output)
        self.assertEqual(prompts, [])
        self.assertEqual(self.path.read_text(), "not JSON")

    def test_failed_initialization_returns_error_without_opening_menu(self):
        with patch.object(Database, "ensure_exists", side_effect=StorageError("denied")):
            code, output, prompts = self.run_cli([])
        self.assertEqual(code, 1)
        self.assertIn("Could not access or save student data", output)
        self.assertEqual(prompts, [])

    def test_eof_and_keyboard_interrupt_exit_cleanly(self):
        for error in (EOFError(), KeyboardInterrupt()):
            code, output, _ = self.run_cli([error])
            self.assertEqual(code, 0)
            self.assertIn("Exiting University System", output)

    def test_password_is_not_in_printed_output(self):
        self.register_existing()
        _, output, _ = self.run_cli(
            ["S", "l", "demo@university.com", "Wrongpass123", "x", "X"]
        )
        self.assertNotIn("Wrongpass123", output)
        self.assertNotIn("Hello123", output)

    def test_import_does_not_start_menu_or_create_files(self):
        project = Path(__file__).resolve().parent.parent
        script = (
            "import sys; from unittest.mock import patch; sys.path.insert(0, sys.argv[1]); "
            "guard = patch('builtins.input', side_effect=AssertionError('unexpected input')); "
            "guard.start(); import uniapp.cli; guard.stop()"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(project)],
            cwd=self.temporary_directory.name,
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual([path.name for path in self.path.parent.iterdir()], ["students.data"])


if __name__ == "__main__":
    unittest.main()
