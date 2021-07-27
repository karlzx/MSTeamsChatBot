# some_file.py
import sys
# insert at 1, 0 is the script path (or '' in REPL)
# sys.path.insert(1, './bots')
from bots import quiz

Student = quiz.Student("n9725342","EGB242_2021_1_")
print("++++++++++ PASS TEST +++++++++++++")
print(Student.get_student_quiz(int("1")))
print(Student.get_student_question())
print(Student.is_valid_quiz_response("A"))
print(Student.is_valid_justification_response("Period is the inverse of frequency"))
print(Student.get_feedback())
print(Student.save_progression())
# print("++++++++++ FAIL TEST +++++++++++++")
# print(Student.get_student_question())
# print(Student.is_valid_quiz_response("B"))
# print(Student.is_valid_justification_response("Period is the inverse of frequency"))
# print(Student.get_feedback())

# TODO TEST UPDATE   

print("++++++++++ END TEST +++++++++++++")
