import random
from uniapp.models import Subject, Student

class SubjectController:

    def generate_mark(self):
        return random.randint(25, 100)

    def generate_unique_id(self, subjects):
        existing_ids = []

        for subject in subjects:
            existing_ids.append(subject.subject_id)

        subject_id = f"{random.randint(1, 999):03d}"

        while subject_id in existing_ids:
            subject_id = f"{random.randint(1, 999):03d}"

        return subject_id

    def calculate_grade(self, mark):
        if mark >= 85:
            return "HD"
        elif mark >= 75:
            return "D"
        elif mark >= 65:
            return "C"
        elif mark >= 50:
            return "P"
        else:
            return "Z"

    def create_subject(self, subjects):
        subject_id = self.generate_unique_id(subjects)
        mark = self.generate_mark()
        grade = self.calculate_grade(mark)

        return Subject(subject_id, mark, grade)

    def enrol_subject(self, student, database):
        if len(student.subjects) >= 4:
            print("Students are allowed to enrol in 4 subjects only")
            return student

        candidate = Student.from_dict(student.to_dict())

        new_subject = self.create_subject(candidate.subjects)
        candidate.subjects.append(new_subject)

        database.update_student(candidate)

        print("Enrolling in Subject-" + new_subject.subject_id)
        print(f"You are now enrolled in {len(candidate.subjects)} out of 4 subjects")
        
        return candidate

    def remove_subject(self, student, database, subject_id):
        candidate = Student.from_dict(student.to_dict())

        for subject in candidate.subjects:
            if subject.subject_id == subject_id:
                candidate.subjects.remove(subject)

                database.update_student(candidate)

                print("Dropping Subject-" + subject_id)
                print(f"You are now enrolled in {len(candidate.subjects)} out of 4 subjects")
                return candidate

        print("Subject not found")
        return student

    def calculate_average(self, student):
        if len(student.subjects) == 0:
            return 0

        total = 0

        for subject in student.subjects:
            total += subject.mark

        return total / len(student.subjects)

    def show_subjects(self, student):
        print(f"Showing {len(student.subjects)} subjects")

        for subject in student.subjects:
            print(
                f"[ Subject::{subject.subject_id} "
                f"-- mark = {subject.mark} "
                f"-- grade = {subject.grade} ]"
            )

        average = self.calculate_average(student)

        print(f"Total subjects: {len(student.subjects)}")
        print(f"Average mark: {average:.2f}")