import csv



class Quiz():
    def __init__(self):
        self.student_qn = []
        self.student_qd = []
        self.quizzes_qn = []
        self.quizzes_qnd = []
        self.nd_array = []
        self.nd_response = ""
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

    def get_update_data(self, quiz_prefix ,student_number):
        self.update_data(quiz_prefix ,student_number)
    # print(remaining)
        for i in range(0,len(self.nd_array)):
            self.nd_response += self.nd_array[i][0] +" "+ self.nd_array[i][1]  + ": Remaining - " +self.nd_array[i][2] +"  \n"
        
        if len(self.nd_response) == 0:
            self.nd_response = "You have completed all assigned quizzes"
        else:
            self.nd_response = "You have the following to finish:  \n" + self.nd_response
        
        print(self.nd_response)
        return self.nd_response 

    def get_quiz_data(self, quiz_prefix ,student_number):
        
        return "Welcome to quiz mode:  \n" +self.get_update_data(quiz_prefix ,student_number) + "  \n" + " Select a quiz"