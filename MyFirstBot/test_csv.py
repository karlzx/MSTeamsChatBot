# some_file.py
import sys
# insert at 1, 0 is the script path (or '' in REPL)
# sys.path.insert(1, './bots')
from bots import quiz

def print_test(stringy):
    print("Test ->>" +str(stringy))

Student = quiz.Student("n9725342","EGB242_2021_1_")
print_test("++++++++++ PASS TEST +++++++++++++")
print_test(Student.get_student_quiz(int("1")))
print_test(Student.get_student_question())
print_test(Student.is_valid_quiz_response("A"))
print_test(Student.is_valid_justification_response("Period is the inverse of frequency"))
print_test(Student.get_feedback())
print_test(Student.save_progression())
# print("++++++++++ FAIL TEST +++++++++++++")
# print(Student.get_student_question())
# print(Student.is_valid_quiz_response("B"))
# print(Student.is_valid_justification_response("Period is the inverse of frequency"))
# print(Student.get_feedback())

# TODO TEST UPDATE   

print("++++++++++ END TEST +++++++++++++")


