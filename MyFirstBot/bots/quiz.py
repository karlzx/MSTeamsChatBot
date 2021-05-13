import csv

class Student():
    def __init__(self, studentNumber = "undefined",quizPrefix = "undefined"):
        self.studentNumber = studentNumber
        self.chatStatus = "greeting"
        self.notDoneArray = [] #table of quizzes not done, columns: [quiz name, quiz due date, remaining questions, total questions]
        self.quizPrefix = quizPrefix
        self.QuizRead = self.QuizRead()
        self.QuestionSet = self.QuestionSet()

    def __read_data(self):
        self.notDoneArray = self.QuizRead.update_student_summary(self.quizPrefix,self.studentNumber)


    ## Method to gather remaining quiz performed data
    def get_student_summary(self):
        self.__read_data()
        
        ndResponse = ""

        for i in range(0,len(self.notDoneArray)):
            ndResponse += self.notDoneArray[i][0] +" "+ self.notDoneArray[i][1]  + ": Remaining - " +self.notDoneArray[i][2] +"  \n"
        
        if len(ndResponse) == 0:
            ndResponse = "You have completed all assigned quizzes"
        else:
            ndResponse = "You have the following to finish:  \n" + ndResponse
        
        return ndResponse 
    
    def get_student_quiz(self, quizNumber):
       
        if (quizNumber > len(self.notDoneArray)) or (quizNumber <= 0):
            return -1
        else:
            setName =self.notDoneArray[quizNumber-1][0]
            currentQ = int(self.notDoneArray[quizNumber-1][3])-int(self.notDoneArray[quizNumber-1][2])
            self.QuestionSet.open_quiz_set(setName,currentQ)
            return setName

    def get_student_question(self):
        return self.QuestionSet.get_latest_question()


    def is_chat_status(self,chatStatus):
        return self.chatStatus == chatStatus
        

    class QuestionSet():
        def __init__(self):
            self.questionSetName = ""
            self.currInd = 0
            # Array of question set info with format:
            # [Question, Image path, A answer, B answer, C answer,d answer, Points, Correct Answer, Correct Justification]
            self.QArray = [] 
            self.currQuestion = ""
            self.currQuestionAnswer = ""
            self.currQuestionPicturePath = ""

        def open_quiz_set(self,setName,currentQind):
            self.questionSetName = setName
            self.currInd = currentQind
            with open('./Data_Quiz/'+ self.questionSetName +'.csv') as csv_qreader:
                    for row in csv_qreader:
                        x = row.split(',')
                        # print(row)
                        if x[6].isdecimal():
                            # row[6] = int(row[6])
                            print(x[6])
                            self.QArray.append(x)
            
            print(self.QArray)

        def get_latest_question(self):
            # print(self.currInd)
            print(self.QArray[0][1])
            return self.QArray[self.currInd][0]
    

    class QuizRead():
        def __init__(self):
            self.student_qn = []    #array of names of quizzes assigned to students (in set) length N
            self.student_qd = []    #array of number of questions student has done per quiz length N
            self.quizzes_qn = []    #array of names of quizzes in set , length N
            self.quizzes_qnd = []   #array of number of questions per quiz, length N
            self.notDoneArray = []      #table of quizzes not done, columns: [quiz name, quiz due date, remaining questions, total questions]
            self.suffix = ".csv"


        def update_student_summary(self, quiz_prefix ,student_number):
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
                            self.notDoneArray.append([assigned,self.quizzes_qnd[qind][1],str(remaining), str(self.quizzes_qnd[qind][0])])


            return self.notDoneArray
            
            

