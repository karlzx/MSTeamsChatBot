import csv

class Student():
    def __init__(self, studentnumber = "undefined",quizprefix = "undefined"):
        self.studentnumber = studentnumber
        self.nd_array = []
        self.quizprefix = quizprefix
        self.Quiz = self.Quiz()

    def read_data(self):
        self.nd_array = self.Quiz.update_data(self.quizprefix,self.studentnumber)

    def get_quiz_info(self):
        return "Welcome to quiz mode:  \n" +self.get_update_data() + "  \n" + " Select a quiz"

    def get_update_data(self):
        self.read_data()
        nd_response = ""

        for i in range(0,len(self.nd_array)):
            nd_response += self.nd_array[i][0] +" "+ self.nd_array[i][1]  + ": Remaining - " +self.nd_array[i][2] +"  \n"
        
        if len(nd_response) == 0:
            nd_response = "You have completed all assigned quizzes"
        else:
            nd_response = "You have the following to finish:  \n" + nd_response
        
        return nd_response 
    
    

    class Quiz():
        def __init__(self):
            self.student_qn = []    #array of names of quizzes assigned to students (in set) length N
            self.student_qd = []    #array of number of questions student has done per quiz length N
            self.quizzes_qn = []    #array of names of quizzes in set , length N
            self.quizzes_qnd = []   #array of number of questions per quiz, length N
            self.nd_array = []      #table of quizzes not done, columns: [quiz name, quiz due date, remaining questions]
            self.suffix = ".csv"


        def update_data(self, quiz_prefix ,student_number):
            self.__init__()
            with open('./Data_Quiz/QuizSummary.csv') as csv_file:
                with open('./Data_Students/' + quiz_prefix + student_number + self.suffix) as csv_student:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    csv_sreader = csv.reader(csv_student, delimiter=',')

                    
                    for row in csv_sreader:
                        if row[1].isdecimal(): 
                            self.student_qn.append(row[0])
                            self.student_qd.append(int(row[1]))
                    for row in csv_reader:
                        if row[1].isdecimal(): 
                            self.quizzes_qn.append(row[0])
                            self.quizzes_qnd.append([int(row[1]),row[2]])
                    
                    for assigned in self.student_qn:
                        stind = self.student_qn.index(assigned)
                        qind = self.quizzes_qn.index(assigned)
                        remaining = self.quizzes_qnd[qind][0]-self.student_qd[stind] 
                        if remaining>0:
                            self.nd_array.append([assigned,self.quizzes_qnd[qind][1],str(remaining)])

            return self.nd_array
            
            

