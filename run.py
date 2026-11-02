from uniapp.admin import admin_menu
from uniapp.cli import main
from uniapp.course_menu import course_menu


if __name__ == "__main__":
    main(admin_handler=admin_menu, enrolment_handler=course_menu)