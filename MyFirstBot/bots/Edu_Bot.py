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
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext,CardFactory
from botbuilder.schema import ChannelAccount

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
        response = Activity(type=ActivityTypes.message)
        
        ##############################################
        # STATE : GREETING
        ##############################################
        # DESC :
        # Starting point of the user. The user can request to do a quiz, request information about their assessments, 
        ##############################################
        if self.Student.is_chat_status("greeting"):
            if self.MLmodel.intent_detected():
                if self.MLmodel.is_user_intent("quiz"):
                    self.Student.set_chat_status("quiz_greeting")

                    response.text = "Welcome to quiz mode:  \n" +self.Student.get_student_summary() + "  \n" + " Select a quiz"
                
                elif self.MLmodel.is_user_intent("quizdetails"):
                    print("getting quiz")
                    
                    response.text =  self.Student.get_student_summary()

                else:
                    response.text = self.MLmodel.pick_response_from_model()
            else:
                response.text = f"I do not understand...."

        ##############################################
        # STATE : QUIZ GREETING
        ##############################################
        # DESC :
        # User is given their available quizzes, and can select to do their desired quiz
        ##############################################
        elif self.Student.is_chat_status("quiz_greeting"):
            if self.MLmodel.intent_detected():
                if self.MLmodel.is_user_intent("quit"):
                    self.Student.set_chat_status("greeting")
                    await turn_context.send_activity("Goodbye!  \n"+ self.Student.get_student_summary())
                    response.text = f"What would you like to do?"

                else:
                    response.text = f"Not supported. Please pick a quiz or type 'quit' to return to home."
            
            elif sentence.isnumeric():
                quizName = self.Student.get_student_quiz(int(sentence))

                if quizName == -1:
                    response.text = f"That is not a valid response, pick again" + "  \n  \n currently:" + self.Student.chatStatus

                else: 
                    # self.Student.get_student_question()
                    await turn_context.send_activity(f"You Requested To do Quiz {quizName}")
                    response.text = self.Student.get_student_question()  + "  \n Please enter your option."
                    response.attachments = [self._get_inline_attachment()]
                    self.Student.set_chat_status("QuizQuestioning") #CHANGE THIS TO quizQuestioning WHEN WORKING

            else:
                response.text = f"I do not understand...." + "  \n  \n currently:" + self.Student.chatStatus

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
                self.Student.set_chat_status("QuizJustifying")
                response.text = "Please Justify Your Answer" + "  \n  \n currently:" + self.Student.chatStatus
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus

        
        ##############################################
        # STATE : QUIZ JUSTIFYING
        ##############################################
        # DESC :
        # User is asked to enter a short answer justification. 
        ##############################################
        elif self.Student.is_chat_status("QuizJustifying"):
            self.justification = sentence
            if self.Student.is_valid_justification_response(sentence):
                self.Student.set_chat_status("QuizConfirming")
                response.text = "Do you confirm? or would you like to change your answer?"  + "  \n  \n currently:" + self.Student.chatStatus
                
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus
        
        ##############################################
        # STATE : QUIZ CONFIRMING
        ##############################################
        # DESC :
        # User is asked to confirm answer. They can either say yes which will submit to pointer checking, or go back to quiz questioning. 
        ##############################################
        elif self.Student.is_chat_status("QuizConfirming"):
            if self.Student.is_valid_confirm_response(sentence) == -1:
                response.text = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus
                
            elif self.Student.is_valid_confirm_response(sentence):# POINTER CHECKING HAPPENS HERE
                feedback = predQ1Model(self.justification)  
                response.text = feedback + "  \n" + "do you want to do another quiz or finish?" + "  \n  \n currently:" + self.Student.chatStatus
                self.Student.set_chat_status("QuizFeedback")
                
            else: 
                response.text = self.Student.get_student_question()  + "  \n Please enter your option."
                self.Student.set_chat_status("QuizQuestioning") 

        ##############################################
        # STATE : QUIZ FEEDBACK
        ##############################################
        # DESC :
        # User is given feedback, they can go on to do more questions or leave the quiz.
        ##############################################

        elif self.Student.is_chat_status("QuizFeedback"):
            if self.Student.is_valid_postfeedback_response(sentence) == -1:
                response.text = "That is not a valid response, please enter try again." + "  \n  \n currently:" + self.Student.chatStatus
            
            elif self.Student.is_valid_postfeedback_response(sentence) == 1:

                response.text = "Here is your next question:" + self.Student.get_student_question()  + "  \n Please enter your option." + "  \n  \n currently:" + self.Student.chatStatus 
                self.Student.chatStatus = "QuizQuestioning" 
                
            elif self.Student.is_valid_postfeedback_response(sentence) == 0:
                self.Student.set_chat_status("quiz_greeting")

                response.text = "Welcome back to quiz mode:  \n" +self.Student.get_student_summary() + "  \n" + " Select a quiz"
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again."+ "  \n  \n currently:" + self.Student.chatStatus

                
        return await turn_context.send_activity(response)


    ##############################################
    # ADDITIONAL FUNCTIONS
    ##############################################              
    def _get_inline_attachment(self) -> Attachment:
        """
        Creates an inline attachment sent from the bot to the user using a base64 string.
        Using a base64 string to send an attachment will not work on all channels.
        Additionally, some channels will only allow certain file types to be sent this way.
        For example a .png file may work but a .pdf file may not on some channels.
        Please consult the channel documentation for specifics.
        :return: Attachment
        """
        file_path = os.path.join(os.getcwd(), "Images/test-picture.png")
        with open(file_path, "rb") as in_file:
            base64_image = base64.b64encode(in_file.read()).decode()

        return Attachment(
            name="PictureQUestion.png",
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
    
    ##############################################
    # ADDITIONAL CLASSES
    ##############################################     
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
        
        # Checks if the user said something that matches an intent built into the model.
        def intent_detected(self):
            return self.prob.item() > self.acceptance_probability

        def is_user_intent(self, intentquery):
            return self.tag == intentquery
        
        def pick_response_from_model(self):
            for intent in self.intents["intents"]:
                        if self.tag == intent["tag"]:
                            return f"{random.choice(intent['responses'])}" 

   
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


                

             
    