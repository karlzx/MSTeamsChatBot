import csv

import numpy as np
import pickle

import os
import urllib.parse
import urllib.request
import base64

from botbuilder.schema import (
    ChannelAccount,
    HeroCard,
    CardAction,
    ActivityTypes,
    Attachment,
    AttachmentData,
    Activity,
    ActionTypes,
)
class Student():
    def __init__(self, studentNumber = "undefined",quizPrefix = "undefined"):
        self.studentNumber = studentNumber
        self.studentName = "Karl"
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
        self.__read_data()
        if (quizNumber > len(self.notDoneArray)) or (quizNumber <= 0):
            return -1
        else:
            setName =self.notDoneArray[quizNumber-1][0]
            currentQ = int(self.notDoneArray[quizNumber-1][3])-int(self.notDoneArray[quizNumber-1][2])
            print("Internal Test -->" + setName)
            self.QuestionSet.open_quiz_set(setName,currentQ)
            return setName

    def get_student_question(self):
        return self.QuestionSet.get_question()
    
    def get_question_picture(self):
        return self.QuestionSet.get_picture()

    def is_valid_quiz_response(self,sentence):
        valid = sentence in self.QuestionSet.MCQLetterOptions
        
        if valid:
            self.temp_MCQresponse = sentence
        
        return valid 

    def is_valid_justification_response(self,sentence):
        #TODO GREATER RESPONSE
        valid = len(sentence)>0
        
        if valid:
            self.temp_MCQJustifications = sentence
        
        return valid

    def is_valid_postfeedback_response(self,sentence):
    #TODO GREATER RESPONSE
        if sentence.lower() == "again":
            return 1
        elif sentence.lower() == "finish":
            return 0
        else:
            return -1

    def is_valid_confirm_response(self,sentence):
        
        if sentence.lower() == "yes":
            return 1
        elif sentence.lower() == "no":
            return 0
        else:
            return -1

    def get_feedback(self):
        textresponse = self.QuestionSet.check_response_and_get_feedback(self.temp_MCQresponse,self.temp_MCQJustifications) 
        textresponse += "  \n" + "do you want to do another quiz or finish?" + "  \n  \n currently:" + self.chatStatus
        return textresponse

    def save_progression(self):
        return self.QuestionSet.commit_to_storage(self.quizPrefix ,self.studentNumber)


    def is_chat_status(self,chatStatus):
        return self.chatStatus == chatStatus

    def set_chat_status(self, newChatStatus):
        self.chatStatus = newChatStatus    
    
    def get_next_question(self):
        self.QuestionSet.update_index()
        self.QuestionSet.update_Question()
        return self.QuestionSet.get_question()

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
            self.MCQfeedback = ""
            self.justificationfeedback =""
            self.pickleName = "NA"
            self.currQuestionAnswer = ""
            self.currQuestionPicturePath = ""
            self.currQuestionOptions = ['N/A']*4
            self.quizSuffix = ".csv"

        def check_response_and_get_feedback(self, MCQresponse, MCQjustification):
            MCQpass = MCQresponse.lower() == self.currQuestionAnswer.lower()
            self.MCQfeedback = "Correct" if MCQpass else  "Incorrect"
            response = "Your MCQ Question was: " + self.MCQfeedback
            print("TEST: PICKLE EXIST")
            # print("./Resources/"+self.pickleName + "vocab.pickle")
            # print(os.path.isfile("./Resources/"+self.pickleName + "vocab.pickle"))
            # print(os.path.isfile("./Resources/"+self.pickleName + "model.pickle"))
            if os.path.isfile("./Resources/Data_Models/"+self.pickleName + "vocab.pickle") and os.path.isfile("./Resources/Data_Models/"+self.pickleName + "model.pickle"):
                self.justificationfeedback = predModel(MCQjustification, self.pickleName)
                response += "  \n" + "And your justification feedback is predicted as: " + self.justificationfeedback
            else: 
                self.justificationfeedback = "Not Found"
            return response

            # TODO: UPDATE SAVE RESPONSE

        def update_student_response(self,mcqresponse,mcqjustification):
            self.currStudentJustification = mcqresponse
            self.currStudentMCQResponse = mcqjustification

        def open_quiz_set(self,setName,currentQind):
            
            self.questionSetName = setName
            self.currInd = currentQind
            print("Internal Test -->" + './Resources/Data_Quiz/'+ self.questionSetName +'.csv')
            self.QArray = [] 
            with open('./Resources/Data_Quiz/'+ self.questionSetName +'.csv') as csv_qreader:
                    for row in csv_qreader:
                        x = row.split(',')
                        # print(row)
                        if x[6].isdecimal():
                            # row[6] = int(row[6])
                            # print(x[6])
                            self.QArray.append(x)


            self.update_Question()

            # print(self.QArray)
        
        def update_index(self):
            self.currInd +=1
            
        def update_Question(self):
            i = self.currInd
            
            self.currQuestion = self.QArray[i][0]
            self.currQuestionPicturePath = self.QArray[i][1]
            self.currQuestionAnswer = self.QArray[i][7]
            self.currQuestionPoints = self.QArray[i][6]
            self.totalQuestions = len(self.QArray)
            self.remainingQuestions = self.totalQuestions - (i+1)
            self.pickleName = str.strip(self.QArray[i][8])
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
    
        def get_picture(self):
            # print(self.currQuestionPicturePath)
            impath = "./Resources/Images/"+self.currQuestionPicturePath + ".png"
            if os.path.isfile(impath):
                return _get_inline_attachment(impath)
            else:
                return -1
        
        def commit_to_storage(self, quiz_prefix ,student_number):
            
            csv_sreader_list = []
            found = False 
            i = 0
            csvpath = './Resources/Data_Students/' + quiz_prefix + student_number + self.quizSuffix
            with open(csvpath) as csv_student:
                csv_sreader = csv.reader(csv_student, delimiter=',')
                csv_sreader_list.extend(csv_sreader)

            for row in csv_sreader_list:
               
                if row[1].isdecimal() and row[0] == self.questionSetName: 
                    found = True
                    break
                i+=1

            if found:
                foundRow = csv_sreader_list[i][:]
                # print(self.questionSetName)
                newCompleted = int(foundRow[1]) +1
                newScore = int(foundRow[2]) + int(self.currQuestionPoints)
                newFeedback = str(foundRow[3]) + " Q"+str(newCompleted)+": "\
                    +"MCQ: " + self.MCQfeedback +", SAR: " + \
                        self.justificationfeedback +"."
                # line_overwrite = {i:[self.questionSetName,newCompleted ,newScore, newFeedback]}
            line_overwrite = [self.questionSetName,newCompleted ,newScore, newFeedback]
            # else: TODO: APPEND 

            # Write data to the csv file and replace the lines in the line_to_override dict.
            with open(csvpath, 'w', newline='') as csv_studentwrite:
                csv_swriter = csv.writer(csv_studentwrite)
                j = 0
                for row in csv_sreader_list:
                    if j == i:
                        csv_swriter.writerow(line_overwrite)
                    else:
                        csv_swriter.writerow(row)
                    j+=1

            return line_overwrite
            

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
            with open('./Resources/Data_Quiz/QuizSummary.csv') as csv_file:
                with open('./Resources/Data_Students/' + quiz_prefix + student_number + self.suffix) as csv_student:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    csv_sreader = csv.reader(csv_student, delimiter=',')

                    
                    for row in csv_sreader:
                        print(row)
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
            
            
def predModel(sentence,picklename):
    ##EXPORTED MODEL
    from sklearn.feature_extraction.text import CountVectorizer
    with open('./Resources/Data_Models/' + picklename +'vocab.pickle', 'rb') as handle:
        model = pickle.load(handle)

    X_list = sentence

    # Clean the data
    from nltk.corpus import stopwords
    from nltk.stem.wordnet import WordNetLemmatizer
    import string
    stop = set(stopwords.words('english'))
    exclude = set(string.punctuation)
    lemma = WordNetLemmatizer()

    def clean(doc):
        stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
        punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
        normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
        return normalized

    X_list_clean = [clean(X_list).split()]
    X_list_clean_comb = []
    for i in range(len(X_list_clean)):
        X_list_clean_comb.append(" ".join(X_list_clean[i]))
    # Create Bag of Words Model
    count_vect = CountVectorizer(stop_words='english')
    X_data = count_vect.fit_transform(X_list_clean_comb)
    X_data = X_data.todense()

    X = X_data

    # Create w2v Model
    X_data_w2v = MeanEmbeddingVectorizer(model).transform(X_list_clean)
    X_data_w2v = np.vstack(X_data_w2v)

    X_w2v = X_data_w2v

    # Load in the pretrained model
    with open('./Resources/Data_Models/'+ picklename + 'model.pickle', 'rb') as handle:
        qmodel = pickle.load(handle)

    prediction = qmodel.predict(X_w2v)

    response = ''

    if prediction == 1:
        response = 'Correct'#. [Note: This feedback is currently in Beta]'
    if prediction == 2:
        response = 'Partly correct'#. [Note: This feedback is currently in Beta]'
    if prediction == 3:
        response = 'Incorrect'#. [Note: This feedback is currently in Beta]'

    return response

class Vectoriser(object):
    def __init__(self, word2vec):
        self.word2vec = word2vec
        # if a text is empty we should return a vector of zeros
        # with the same dimensionality as all the other vectors
        self.dim = 300  # This is the dimentions which the Google News Vector contains.


    def transform(self, X):
        X_ret = []
        for words in X:
            average = []
            for w in words:
                if w in self.word2vec:
                    average.append(self.word2vec[w])
            average = np.mean(average or [np.zeros(self.dim)] , axis=0)
            norm2 = (np.linalg.norm(average, ord=2) + 1e-6)
            average = average / norm2
            #if np.mean(average) != 0:
            #    average = average - np.mean(average)
            #    average = average / np.std(average)
            X_ret.append(average)

        return X_ret

class MeanEmbeddingVectorizer(Vectoriser):

    def fit(self, X, y):
        return self


##############################################
# ADDITIONAL FUNCTIONS
##############################################              
def _get_inline_attachment(impath) -> Attachment:
    """
    Creates an inline attachment sent from the bot to the user using a base64 string.
    Using a base64 string to send an attachment will not work on all channels.
    Additionally, some channels will only allow certain file types to be sent this way.
    For example a .png file may work but a .pdf file may not on some channels.
    Please consult the channel documentation for specifics.
    :return: Attachment
    """
    file_path = os.path.join(os.getcwd(), impath)
    with open(file_path, "rb") as in_file:
        base64_image = base64.b64encode(in_file.read()).decode()

    return Attachment(
        name="PictureQuestion.png",
        content_type="image/png",
        content_url=f"data:image/png;base64,{base64_image}",
    )
def _get_internet_attachment(self) -> Attachment:
    """
    Creates an Attachment to be sent from the bot to the user from a HTTP URL.
    :return: Attachment
    """
    return Attachment(
        name="architecture-resize.png",
        content_type="image/png",
        content_url="https://docs.microsoft.com/en-us/bot-framework/media/how-it-works/architecture-resize.png",
    )