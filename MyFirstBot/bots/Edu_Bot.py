# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import random
import json
import torch
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
        self.MLmodel = self.MLmodel()

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hi I'm Ed the Educational Bot! type 'quit' to exit")
                self.Student = quiz.Student("n9725342","EGB242_2021_1_")
                
    

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
                    # response.attachments = [self._get_inline_attachment()]
                    picture = self.Student.get_question_picture()
                    print(picture)
                    if picture != -1:
                        response.attachments = [picture]
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
                response.text = self.Student.get_feedback() 
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

                response.text = "Here is your next question:" + self.Student.get_student_question()  + "  \n Please enter your option."  + "  \n  \n currently:" + self.Student.chatStatus

                picture = self.Student.get_question_picture()
                if picture != -1:
                    response.attachments = [picture]
               
                self.Student.set_chat_status("QuizQuestioning")
                
            elif self.Student.is_valid_postfeedback_response(sentence) == 0:
                self.Student.set_chat_status("quiz_greeting")

                response.text = "Welcome back to quiz mode:  \n" +self.Student.get_student_summary() + "  \n" + " Select a quiz"
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again."+ "  \n  \n currently:" + self.Student.chatStatus

                
        return await turn_context.send_activity(response)


    
    ##############################################
    # ADDITIONAL CLASSES
    ##############################################     
    class MLmodel():
        def __init__(self):
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            with open('./Resources/intents.json','r') as f:
                self.intents = json.load(f)

            FILE = "./Resources/data.pth"

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


                

             
    