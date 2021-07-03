# some_file.py
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, './bots')

import quiz

Student = quiz.Student("n9725342","EGB242_2021_1_")
print("++++++++++ START TEST +++++++++++++")
print(Student.get_student_quiz(int("1")))
print(Student.get_student_question())
print(Student.is_valid_quiz_response("A"))
print(Student.is_valid_justification_response("Period is the inverse of frequency"))

print(Student.is_valid_justification_response("Period is the inverse of frequency"))


print("++++++++++ END TEST +++++++++++++")
