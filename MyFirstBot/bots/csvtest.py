import pandas as pd
import csv
# df = pd.read_csv('./Data_Quiz/QuizSummary.csv')

# for x in range(0,len( df.loc[:,['Quiz']])):
#     print(df.loc[x,['Quiz']] ) 

quiz_prefix = "EGB242_2021_1_"
student_number = "n9725342"
suffix = ".csv"


with open('./Data_Quiz/QuizSummary.csv') as csv_file:
    with open('./Data_Students/' +quiz_prefix+ student_number + suffix) as csv_student:
        csv_reader = csv.reader(csv_file, delimiter=',')
        csv_sreader = csv.reader(csv_student, delimiter=',')

        student_qn = []
        student_qd = []
        quizzes_qn = []
        quizzes_qnd = []
        not_done = []
        nd_response = ""
        for row in csv_sreader:
            if row[1].isdecimal(): 
                student_qn.append(row[0])
                student_qd.append(int(row[1]))
        for row in csv_reader:
            if row[1].isdecimal(): 
                quizzes_qn.append(row[0])
                quizzes_qnd.append([int(row[1]),row[2]])
        
        for assigned in student_qn:
            stind = student_qn.index(assigned)
            qind = quizzes_qn.index(assigned)
            remaining = quizzes_qnd[qind][0]-student_qd[stind] 
            # print(remaining)
            if remaining>0:
                nd_response += assigned +" "+ quizzes_qnd[qind][1]  + ": Remaining - " +str(remaining) +"\n"
                # not_done.append([assigned, remaining, quizzes_qnd[qind][1]])
        
        print(nd_response)
        # for i in range(0,len(quizzes_available))
        # print(quizzes_available)
        # for row in csv_sreader:
        #     print(row[0] + " " + row[1])
