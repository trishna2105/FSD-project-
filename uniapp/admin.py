from uniapp.enrolment import SubjectController
from uniapp.errors import DataFormatError, StorageError, StudentNotFoundError

controller = SubjectController()


def get_grade(student):
    return controller.calculate_grade(controller.calculate_average(student))


def format_student(student):
    average = controller.calculate_average(student)
    return (
        f"{student.name} :: {student.student_id} --> "
        f"GRADE: {get_grade(student):>2} - MARK: {average:.2f}"
    )


def show_students(database):
    students = database.read_all()
    print("\tStudent List")
    if len(students) == 0:
        print("\t\t< Nothing to Display >")
        return
    for student in students:
        print(f"\t{student.name} :: {student.student_id} --> Email: {student.email}")


def group_students(database):
    students = database.read_all()
    print("\tGrade Grouping")
    if len(students) == 0:
        print("\t\t< Nothing to Display >")
        return

    groups = {"Z": [], "P": [], "C": [], "D": [], "HD": []}
    for student in students:
        groups[get_grade(student)].append(student)

    for grade, members in groups.items():
        if len(members) > 0:
            text = ", ".join(format_student(student) for student in members)
            print(f"\t{grade:<2} --> [{text}]")


def partition_students(database):
    students = database.read_all()
    passed = []
    failed = []
    for student in students:
        if controller.calculate_average(student) >= 50:
            passed.append(student)
        else:
            failed.append(student)

    print("\tPASS/FAIL Partition")
    print("\tFAIL --> [" + ", ".join(format_student(s) for s in failed) + "]")
    print("\tPASS --> [" + ", ".join(format_student(s) for s in passed) + "]")


def remove_student(database):
    student_id = input("\tRemove by ID: ").strip()
    try:
        database.delete_student(student_id)
    except StudentNotFoundError:
        print(f"\tStudent {student_id} does not exist")
        return
    print(f"\tRemoving Student {student_id} Account")


def clear_database(database):
    print("\tClearing students database")
    answer = input("\tAre you sure you want to clear the database (Y)ES/(N)O: ").strip().lower()
    if answer == "y":
        database.clear()
        print("\tStudents data cleared")


def show_data_error(error):
    if isinstance(error, DataFormatError):
        print("\tStudent data is invalid. The file has not been reset.")
    else:
        print("\tCould not access or save student data. Please try again.")


def admin_menu(database):
    actions = {
        "c": clear_database,
        "g": group_students,
        "p": partition_students,
        "r": remove_student,
        "s": show_students,
    }
    while True:
        choice = input("\tAdmin System (c/g/p/r/s/x): ").strip().lower()
        if choice == "x":
            return
        if choice not in actions:
            print("\tInvalid option, please try again")
            continue
        try:
            actions[choice](database)
        except (DataFormatError, StorageError) as error:
            show_data_error(error)