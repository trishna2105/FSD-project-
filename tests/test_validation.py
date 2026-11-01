import unittest

from uniapp.errors import ValidationError
from uniapp.validation import (
    normalize_email,
    validate_email,
    validate_name,
    validate_password,
)


class ValidationTests(unittest.TestCase):
    def test_email_is_trimmed_and_lowercased(self):
        self.assertEqual(
            normalize_email("  Demo.Student@UNIVERSITY.COM \t"),
            "demo.student@university.com",
        )

    def test_email_normalization_is_idempotent(self):
        email = normalize_email(" Demo@UNIVERSITY.COM ")
        self.assertEqual(normalize_email(email), email)

    def test_valid_email_formats(self):
        for email in (
            "demo@university.com",
            "demo.student@university.com",
            "demo_student+test-1@university.com",
            "123@university.com",
            " Demo@UNIVERSITY.COM ",
        ):
            with self.subTest(email=email):
                self.assertIsNone(validate_email(email))

    def test_invalid_email_formats(self):
        for email in (
            "@university.com",
            "demo@gmail.com",
            "demo@universityXcom",
            "demo@university.com.evil",
            "demo@@university.com",
            "demo student@university.com",
            "demo\nstudent@university.com",
            ".demo@university.com",
            "demo.@university.com",
            "demo..student@university.com",
            "데모@university.com",
        ):
            with self.subTest(email=email):
                with self.assertRaises(ValidationError) as error:
                    validate_email(email)
                self.assertEqual(error.exception.field, "email")
                self.assertEqual(error.exception.reason, "invalid_format")

    def test_normalization_does_not_replace_format_validation(self):
        self.assertEqual(normalize_email(" Demo@OTHER.COM "), "demo@other.com")
        with self.assertRaises(ValidationError):
            validate_email(" Demo@OTHER.COM ")

    def test_password_letter_boundary(self):
        with self.assertRaises(ValidationError):
            validate_password("Hell123")
        self.assertIsNone(validate_password("Hello123"))
        self.assertIsNone(validate_password("Hellow123"))

    def test_password_digit_boundary(self):
        with self.assertRaises(ValidationError):
            validate_password("Hello12")
        self.assertIsNone(validate_password("Hello123"))
        self.assertIsNone(validate_password("Hello1234"))

    def test_valid_passwords_allow_mixed_case_letters(self):
        for password in ("Helloworld123", "HELLOW123", "HelloWorld12345"):
            with self.subTest(password=password):
                self.assertIsNone(validate_password(password))

    def test_invalid_password_formats(self):
        # Avoid placing credentials in subtest labels or failure messages.
        for password in (
            "helloworld123",
            "1Helloworld123",
            "Helloworld123a",
            "Helloworld12!",
            "Hello1world23",
            "Helloworld１２３",
            "Hélloworld123",
        ):
            with self.assertRaises(ValidationError) as error:
                validate_password(password)
            self.assertEqual(error.exception.field, "password")
            self.assertEqual(error.exception.reason, "invalid_format")

    def test_password_whitespace_is_not_stripped(self):
        for password in (
            " Helloworld123",
            "Helloworld123 ",
            "Helloworld123\n",
            "Helloworld\t123",
        ):
            with self.assertRaises(ValidationError):
                validate_password(password)

    def test_valid_names_allow_unicode_and_surrounding_spaces(self):
        for name in ("Demo Student", "김학생", "O'Connor", "  Demo Student  "):
            with self.subTest(name=name):
                self.assertIsNone(validate_name(name))

    def test_empty_input_has_required_reason(self):
        for field, validator in (
            ("name", validate_name),
            ("email", validate_email),
            ("password", validate_password),
        ):
            for value in ("", "   ", "\t\n"):
                with self.subTest(field=field):
                    with self.assertRaises(ValidationError) as error:
                        validator(value)
                    self.assertEqual(error.exception.field, field)
                    self.assertEqual(error.exception.reason, "required")

    def test_non_string_input_has_invalid_type_reason(self):
        for field, validator in (
            ("name", validate_name),
            ("email", validate_email),
            ("password", validate_password),
        ):
            for value in (None, 123, True, [], {}):
                with self.subTest(field=field):
                    with self.assertRaises(ValidationError) as error:
                        validator(value)
                    self.assertEqual(error.exception.field, field)
                    self.assertEqual(error.exception.reason, "invalid_type")

    def test_normalization_rejects_invalid_input(self):
        for value in (None, 123, "", "   "):
            with self.assertRaises(ValidationError):
                normalize_email(value)

    def test_password_error_does_not_include_input(self):
        password = "PrivateInvalidPassword!"
        with self.assertRaises(ValidationError) as error:
            validate_password(password)
        self.assertEqual(str(error.exception), "password: invalid_format")
        self.assertNotIn(password, str(error.exception))
        self.assertNotIn(password, repr(error.exception))


if __name__ == "__main__":
    unittest.main()
