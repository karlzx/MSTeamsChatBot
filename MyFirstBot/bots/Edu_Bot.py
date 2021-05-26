# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import random
import json
import torch
import pickle
import numpy as np
from . import quiz
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount

# quiz_prefix = 
# student_number = "n9725342"

# student_number = "n9725342"

# Quiz = quiz.Quiz()


class EduBot(ActivityHandler):
    def __init__(self):
        self.bot_name = "Ed"
        self.Student = quiz.Student("n9725342","EGB242_2021_1_")
        self.MLmodel = self.MLmodel()

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hi I'm Ed the Educational Bot! type 'quit' to exit")
    

    async def on_message_activity(self, turn_context: TurnContext):
        sentence = turn_context.activity.text
        
        # Acquire Response
        self.MLmodel.update_prob(sentence)

        print(f"Current state {self.Student.chatStatus}")

        print(f"User said {sentence}. gathered: intent {self.MLmodel.tag} with probability {self.MLmodel.prob.item()}")

        ##############################################
        # STATE : GREETING
        ##############################################
        # DESC :
        # User can request for quiz, request for info
        #
        ##############################################
        if self.Student.is_chat_status("greeting"):
            if self.MLmodel.prob.item() > self.MLmodel.acceptance_probability:
                if self.MLmodel.tag == "quiz":
                    self.Student.chatStatus = "quiz_greeting"
                    response = "Welcome to quiz mode:  \n" +self.Student.get_student_summary() + "  \n" + " Select a quiz"
                
                elif self.MLmodel.tag == "quizdetails":
                    print("getting quiz")
                    response =  self.Student.get_student_summary()

                else:
                    for intent in self.MLmodel.intents["intents"]:
                        if self.MLmodel.tag == intent["tag"]:
                            response = f"{random.choice(intent['responses'])}" 
            else:
                response = f"I do not understand...."

        ##############################################
        # STATE : QUIZ GREETING
        ##############################################
        # DESC :
        # User is displayed what quizzes there are, and enter into a quiz
        ##############################################
        elif self.Student.is_chat_status("quiz_greeting"):
            if self.MLmodel.prob.item() > self.MLmodel.acceptance_probability:
                if self.MLmodel.tag == "quit":
                    self.Student.chatStatus = "greeting"
                    await turn_context.send_activity("Goodbye!  \n"+ self.Student.get_student_summary())
                    response = f"What would you like to do?"
                else:
                    response = f"Not supported. Please pick a quiz or type 'quit' to return to home."
            
            elif sentence.isnumeric():
                quizName = self.Student.get_student_quiz(int(sentence))

                if quizName == -1:
                    response = f"That is not a valid response, pick again" + "  \n  \n currently:" + self.Student.chatStatus

                else: 
                    # self.Student.get_student_question()
                    await turn_context.send_activity(f"You Requested To do Quiz {quizName}")
                    response = self.Student.get_student_question()  + "  \n Please enter your option."
                    self.Student.chatStatus = "QuizQuestioning" #CHANGE THIS TO quizQuestioning WHEN WORKING

            else:
                response = f"I do not understand...." + "  \n  \n currently:" + self.Student.chatStatus

        ##############################################
        # STATE : QUIZ QUESTIONING
        ##############################################
        # DESC :
        # User is given a question
        # Response should be a letter response to. passes onto justification if a valid response
        ##############################################
        elif  self.Student.is_chat_status("QuizQuestioning"):
            # send details when you get into quiz as an await.
            if self.Student.is_valid_quiz_response(sentence): 
                self.Student.chatStatus = "QuizJustifying" 
                response = "Please Justify Your Answer" + "  \n  \n currently:" + self.Student.chatStatus
            #  TODO: QUIT 
            else:
                response = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus

        
        ##############################################
        # STATE : QUIZ QUESTIONING
        ##############################################
        # DESC :
        # User is given a question
        # Response should be a letter response to. passes onto justification if a valid response
        ##############################################
        elif self.Student.is_chat_status("QuizJustifying"):
            self.justification = sentence
            if self.Student.is_valid_justification_response(sentence):
                self.Student.chatStatus = "QuizConfirming"
                response = "Do you confirm? or would you like to change your answer?"  + "  \n  \n currently:" + self.Student.chatStatus
                
            
            #  TODO: QUIT 
            else:
                response = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus
        

        elif self.Student.is_chat_status("QuizConfirming"):
            if self.Student.is_valid_justification_response(sentence):
                # POINTER CHECKING HAPPENS HERE
                self.Student.chatStatus = "QuizFeedback"
                feedback = predQ1Model(self.justification)  
                response = feedback + "  \n" + "do you want to do another quiz or finish?" + "  \n  \n currently:" + self.Student.chatStatus
                
            #  TODO: QUIT 
            else:
                response = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus


        elif self.Student.is_chat_status("QuizFeedback"):
            if self.Student.is_valid_justification_response(sentence):

                response = "Here is your other question:" + self.Student.get_student_question()  + "  \n Please enter your option." + "  \n  \n currently:" + self.Student.chatStatus 
                self.Student.chatStatus = "QuizQuestioning" 
                
            
            #  TODO: QUIT 
            else:
                response = "That is not a valid response, please enter try again."+ "  \n  \n currently:" + self.Student.chatStatus


                
        return await turn_context.send_activity(MessageFactory.text(f"{response}"))
                        

    class MLmodel():
        def __init__(self):
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            with open('intents.json','r') as f:
                self.intents = json.load(f)

            FILE = "data.pth"

            data = torch.load(FILE,map_location='cpu')

            self.input_size = data["input_size"]
            self.hidden_size = data["hidden_size"]
            self.output_size = data["output_size"]
            self.all_words = data["all_words"]
            self.tags = data["tags"]
            self.model_state = data["model_state"]


            self.model = NeuralNet( self.input_size,  self.hidden_size,  self.output_size).to( self.device)
            self.model.load_state_dict( self.model_state)
            self.model.eval()

        def update_prob(self,sentence):
            self.tokenizedSentence = tokenize(sentence)
            X = bag_of_words(self.tokenizedSentence, self.all_words)
            X = X.reshape(1,X.shape[0])
            X = torch.from_numpy(X).to(self.device)
            output = self.model(X)
            _,predicted = torch.max(output, dim=1)

            self.tag = self.tags[predicted.item()]

            probs = torch.softmax(output, dim = 1)
            self.prob = probs[0][predicted.item()]
            self.acceptance_probability = 0.75

def predQ1Model(sentence):
    ##EXPORTED MODEL
    from sklearn.feature_extraction.text import CountVectorizer
    with open('vocab.pickle', 'rb') as handle:
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
    with open('q1model.pickle', 'rb') as handle:
        qmodel = pickle.load(handle)

    prediction = qmodel.predict(X_w2v)

    response = ''

    if prediction == 1:
        response = 'Your Conceptual Understanding for Question 1 was predicted as correct. [Note: This feedback is currently in Beta]'
    if prediction == 2:
        response = 'Your Conceptual Understanding for Question 1 was predicted as partly correct. [Note: This feedback is currently in Beta]'
    if prediction == 3:
        response = 'Your Conceptual Understanding for Question 1 was predicted as incorrect. [Note: This feedback is currently in Beta]'

    return response

class MeanEmbeddingVectorizer(object):
    def __init__(self, word2vec):
        self.word2vec = word2vec
        # if a text is empty we should return a vector of zeros
        # with the same dimensionality as all the other vectors
        self.dim = len(next(iter(self.word2vec.items())))

    def fit(self, X, y):
        return self

    def transform(self, X):
        return np.array([
            np.mean([self.word2vec[w] for w in words if w in self.word2vec]
                    or [np.zeros(self.dim)], axis=0)
            for words in X
        ])

# if __name__ == "__main__":

#     #Export vocab for each question before looking
#     #exportQ1Vocab()

#     #Create model for each question
#     #createQ1Model()

#     #Test some example setences prediction
#     sentence1 = 'Frequency is the inverse of period' #Should be 1
#     sentence2 = 'guess' #Should be 3
#     sentence3 = 'Random words I am typing' #Should be 3
#     sentence4 = 'The amplitude is higher' #Should be 3
#     sentence5 = 'Option (a) has the greatest frequency, as the cycles oscillate the most.'  # Should be 3
#     sentence6 = 'The signal frequency amplitude period is the highest in time.'
#     sentence7 = 'The amplitude is the largest'
    
#     out1 = predQ1Model(sentence1)   


                

             
    