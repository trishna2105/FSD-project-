import tempfile
from pathlib import Path

from uniapp.database import Database
from uniapp.models import Student
from uniapp.enrolment import SubjectController


with tempfile.TemporaryDirectory() as folder:
    database = Database(Path(folder) / "test_students.data")
    database.ensure_exists()

    student = Student(
        student_id="123456",
        name="Test Student",
        email="test@university.com",
        password="Hello123"
    )

    database.add_student(student)

    controller = SubjectController()

    for i in range(5):
        student = controller.enrol_subject(student, database)

    saved_student = database.find_by_id("123456")

    print("Total subjects:", len(saved_student.subjects))

    for subject in saved_student.subjects:
        print(subject.subject_id, subject.mark, subject.grade)

    subject_id = student.subjects[0].subject_id

    student = controller.remove_subject(student, database, subject_id)

    saved_student = database.find_by_id("123456")

    print("Removed Subject ID:", subject_id)
    print("Total subjects after removal:", len(saved_student.subjects))

    print("\n--- Show Subjects Test ---")
    controller.show_subjects(student)

    print("\n--- Average Test ---")
    print("Average:", controller.calculate_average(student))