# admin_controller.py - Admin subsystem for CLIUniApp
# Needs Student objects with: .id, .name, .email, .subjects
# and Subject objects with: .mark

import os
import pickle

FILE_NAME = "students.data"


# ---- Only change these 2 functions to use the team's Database class ----
def load_students():
    """Return the list of Student objects stored in students.data."""
    if not os.path.exists(FILE_NAME) or os.path.getsize(FILE_NAME) == 0:
        return []
    with open(FILE_NAME, "rb") as f:
        return pickle.load(f)


def save_students(students):
    """Write the list of Student objects to students.data."""
    with open(FILE_NAME, "wb") as f:
        pickle.dump(students, f)
# ------------------------------------------------------------------------


def get_average(student):
    """Average mark of all the student's subjects (0 if none)."""
    if len(student.subjects) == 0:
        return 0
    total = 0
    for subject in student.subjects:
        total += subject.mark
    return total / len(student.subjects)


def get_grade(mark):
    """UTS grading: Z < 50 <= P < 65 <= C < 75 <= D < 85 <= HD"""
    if mark >= 85:
        return "HD"
    elif mark >= 75:
        return "D"
    elif mark >= 65:
        return "C"
    elif mark >= 50:
        return "P"
    return "Z"


def format_student(student):
    """Example: Alen Jones :: 762740 --> GRADE:  P - MARK: 63.50"""
    avg = get_average(student)
    return f"{student.name} :: {student.id} --> GRADE: {get_grade(avg):>2} - MARK: {avg:.2f}"


def show_students():
    print("\tStudent List")
    students = load_students()
    if len(students) == 0:
        print("\t\t< Nothing to Display >")
        return
    for s in students:
        print(f"\t{s.name} :: {s.id} --> Email: {s.email}")


def group_students():
    print("\tGrade Grouping")
    students = load_students()
    if len(students) == 0:
        print("\t\t< Nothing to Display >")
        return

    groups = {"Z": [], "P": [], "C": [], "D": [], "HD": []}
    for s in students:
        groups[get_grade(get_average(s))].append(s)

    for grade, members in groups.items():
        if len(members) > 0:
            text = ", ".join(format_student(s) for s in members)
            print(f"\t{grade:<2} --> [{text}]")


def partition_students():
    print("\tPASS/FAIL Partition")
    students = load_students()

    passed = []
    failed = []
    for s in students:
        if get_average(s) >= 50:
            passed.append(s)
        else:
            failed.append(s)

    print("\tFAIL --> [" + ", ".join(format_student(s) for s in failed) + "]")
    print("\tPASS --> [" + ", ".join(format_student(s) for s in passed) + "]")


def remove_student():
    student_id = input("\tRemove by ID: ").strip()
    students = load_students()

    for s in students:
        if str(s.id).zfill(6) == student_id.zfill(6):
            students.remove(s)
            save_students(students)
            print(f"\tRemoving Student {student_id} Account")
            return
    print(f"\tStudent {student_id} does not exist")


def clear_database():
    print("\tClearing students database")
    answer = input("\tAre you sure you want to clear the database (Y)ES/(N)O: ").strip().lower()
    if answer == "y":
        save_students([])
        print("\tStudents data cleared")


def admin_menu():
    """Call this from the University menu when the user picks A."""
    while True:
        choice = input("\tAdmin System (c/g/p/r/s/x): ").strip().lower()

        if choice == "c":
            clear_database()
        elif choice == "g":
            group_students()
        elif choice == "p":
            partition_students()
        elif choice == "r":
            remove_student()
        elif choice == "s":
            show_students()
        elif choice == "x":
            break
        else:
            print("\tInvalid option, please try again")


if __name__ == "__main__":
    admin_menu()
