import json
import unittest

from uniapp.errors import DataFormatError
from uniapp.models import Student, Subject


class ModelTests(unittest.TestCase):
    def student_data(self):
        return {
            "student_id": "000123",
            "name": "Demo Student",
            "email": "demo.student@university.com",
            "password": "Examplepass123",
            "subjects": [{"subject_id": "007", "mark": 85, "grade": "HD"}],
        }

    def test_json_round_trip_preserves_nested_data(self):
        data = self.student_data()
        student = Student.from_dict(data)
        restored = Student.from_dict(json.loads(json.dumps(student.to_dict())))
        self.assertEqual(restored.to_dict(), data)
        self.assertIsInstance(restored.subjects[0], Subject)
        self.assertIsNot(restored.subjects[0], student.subjects[0])

    def test_default_subject_lists_are_independent(self):
        first = Student("000001", "First", "first@university.com", "Examplepass123")
        second = Student("000002", "Second", "second@university.com", "Examplepass123")
        first.subjects.append(Subject("001", 50, "P"))
        self.assertEqual(second.subjects, [])

    def test_restored_objects_do_not_modify_input(self):
        data = self.student_data()
        student = Student.from_dict(data)
        student.subjects[0].mark = 90
        student.subjects.clear()
        self.assertEqual(data["subjects"], [{"subject_id": "007", "mark": 85, "grade": "HD"}])

    def test_serialized_objects_do_not_modify_model(self):
        student = Student.from_dict(self.student_data())
        data = student.to_dict()
        data["subjects"][0]["mark"] = 90
        self.assertEqual(student.subjects[0].mark, 85)

    def test_password_is_excluded_from_repr(self):
        student = Student.from_dict(self.student_data())
        self.assertNotIn(student.password, repr(student))

    def test_invalid_student_ids_are_rejected(self):
        for student_id in ("000000", "12345", "1234567", "１２３４５６", 123456, None):
            with self.subTest(student_id=student_id):
                data = self.student_data()
                data["student_id"] = student_id
                with self.assertRaises(DataFormatError):
                    Student.from_dict(data)

    def test_id_boundaries_are_preserved(self):
        for student_id in ("000001", "999999"):
            data = self.student_data()
            data["student_id"] = student_id
            self.assertEqual(Student.from_dict(data).student_id, student_id)
        for subject_id in ("001", "999"):
            self.assertEqual(Subject(subject_id, 25, "Z").subject_id, subject_id)

    def test_invalid_subject_data_is_rejected(self):
        for field, values in (
            ("subject_id", ("000", "01", "1000", "１２３", 7)),
            ("mark", (24, 101, True, 85.0, "85", None)),
            ("grade", ("A", "hd", None, [])),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    data = {"subject_id": "007", "mark": 85, "grade": "HD"}
                    data[field] = value
                    with self.assertRaises(DataFormatError):
                        Subject.from_dict(data)

    def test_missing_and_unknown_fields_are_rejected(self):
        for field in self.student_data():
            data = self.student_data()
            del data[field]
            with self.subTest(missing=field), self.assertRaises(DataFormatError):
                Student.from_dict(data)
        data = self.student_data()
        data["unexpected"] = "value"
        with self.assertRaises(DataFormatError):
            Student.from_dict(data)
        for subject in ({"subject_id": "007", "mark": 85},
                        {"subject_id": "007", "mark": 85, "grade": "HD", "extra": 1}):
            with self.assertRaises(DataFormatError):
                Subject.from_dict(subject)

    def test_invalid_containers_are_rejected(self):
        for data in (None, [], "student"):
            with self.subTest(data=data), self.assertRaises(DataFormatError):
                Student.from_dict(data)
        for subjects in (None, {}, [None], ["subject"]):
            data = self.student_data()
            data["subjects"] = subjects
            with self.subTest(subjects=subjects), self.assertRaises(DataFormatError):
                Student.from_dict(data)

    def test_invalid_student_text_is_rejected_without_exposing_values(self):
        for field in ("name", "email", "password"):
            for value in (None, 123, "", "   "):
                data = self.student_data()
                data[field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaises(DataFormatError) as error:
                        Student.from_dict(data)
                    self.assertNotIn("Examplepass123", str(error.exception))

    def test_duplicate_subjects_and_fifth_subject_are_rejected(self):
        data = self.student_data()
        data["subjects"] *= 2
        with self.assertRaises(DataFormatError):
            Student.from_dict(data)
        data["subjects"] = [
            {"subject_id": f"{number:03d}", "mark": 85, "grade": "HD"}
            for number in range(1, 5)
        ]
        self.assertEqual(len(Student.from_dict(data).subjects), 4)
        data["subjects"].append({"subject_id": "005", "mark": 85, "grade": "HD"})
        with self.assertRaises(DataFormatError):
            Student.from_dict(data)

    def test_mutated_invalid_data_is_rejected_before_serialization(self):
        student = Student.from_dict(self.student_data())
        student.subjects[0].mark = True
        with self.assertRaises(DataFormatError):
            student.to_dict()
        student = Student.from_dict(self.student_data())
        student.subjects.append({"subject_id": "008", "mark": 50, "grade": "P"})
        with self.assertRaises(DataFormatError):
            student.to_dict()


if __name__ == "__main__":
    unittest.main()
