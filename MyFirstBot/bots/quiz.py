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
        return self.QuestionSet.get_question()

    def is_valid_quiz_response(self,sentence):
        return sentence in self.QuestionSet.MCQLetterOptions

    def is_valid_justification_response(self,sentence):
        #TODO GREATER RESPONSE
        return len(sentence)>0

    def is_valid_confirm_response(self,sentence):
        
        if sentence.lower() == "yes":
            return 1
        elif sentence.lower() == "no":
            return 0
        else:
            return -1

    def check_correct_answer(self,sentence):
        return self.QuestionSet.currQuestionAnswer == sentence


    def is_chat_status(self,chatStatus):
        return self.chatStatus == chatStatus
        

    class QuestionSet():
        def __init__(self):
            self.questionSetName = ""
            self.currInd = 0
            self.MCQLetterOptions = ['A','B','C','D']
            self.MaxMCQOptions = 4
            # Array of question set info with format:
            # [Question, Image path, A answer, B answer, C answer,d answer, Points, Correct Answer, Correct Justification]
            self.QArray = [] 

            self.currQuestion = ""
            self.currQuestionAnswer = ""
            self.currQuestionPicturePath = ""
            self.currQuestionOptions = ['N/A']*4

        def open_quiz_set(self,setName,currentQind):
            self.questionSetName = setName
            self.currInd = currentQind
            with open('./Data_Quiz/'+ self.questionSetName +'.csv') as csv_qreader:
                    for row in csv_qreader:
                        x = row.split(',')
                        # print(row)
                        if x[6].isdecimal():
                            # row[6] = int(row[6])
                            # print(x[6])
                            self.QArray.append(x)


            self.update_Question()

            print(self.QArray)
        
        def update_Question(self):
            i = self.currInd
            
            self.currQuestion = self.QArray[i][0]
            self.currQuestionPicturePath = self.QArray[i][1]
            self.currQuestionAnswer = self.QArray[i][7]
            self.currQuestionPoints = self.QArray[i][6]
            for j in range(0,self.MaxMCQOptions):
                self.currQuestionOptions[j] = self.QArray[i][2+j]
            # for j in range(0,len(self.QArray[i])):
                # print(self.QArray[i][j])
                # self.QArray[i]
                # self.currQuestionOptions[i] = self.QArray[i][2+j]

        def get_question(self):
            # print(self.currInd)
            response = f"Question {self.currInd + 1}:  \n" + self.currQuestion + "  \n"
            for i in range(0,self.MaxMCQOptions):
                response += self.MCQLetterOptions[i] + ": " + self.currQuestionOptions[i] + "  \n"
            return response 
    

    class QuizRead():
        def __init__(self):
            self.student_qn = []    #array of names of quizzes assigned to students (in set) length N
            self.student_qd = []    #array of number of questions student has done per quiz length N
            self.quizzes_qn = []    #array of names of quizzes in set , length N
            self.quizzes_qnd = []   #array of number of questions per quiz, length N
            self.notDoneArray = []      #table of quizzes not done, columns: [quiz name, quiz due date, remaining questions, total questions]
            self.suffix = ".csv"


        def update_student_summary(self, quiz_prefix ,student_number):
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
                            self.notDoneArray.append([assigned,self.quizzes_qnd[qind][1],str(remaining), str(self.quizzes_qnd[qind][0])])


            return self.notDoneArray
            
            

