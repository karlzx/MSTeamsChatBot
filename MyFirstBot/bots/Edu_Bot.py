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
                self.Student = quiz.Student("n9725342","EGB242_2021_1_")
                await turn_context.send_activity("Hi " +self.Student.studentName + ", I'm Ed the Educational Bot! Type 'help' to see what you can do!")
                #  + \
                #         + "  \n  \n" + "You can ask me to do the following:  \n" \
                #         +"'I want to do a quiz' to perform a quiz.  \n"\
                #         +"'When are my quizzes due?' to check your quiz due dates.  \n"\
                #         +"'Who is my course coordinator?' to see relevant staff information.  \n  \n" \
                #         +"If you need assistance with your uni work, please contact your Lecturer, Tutor, HiQ, or the faculty! or type 'help' to see this prompt again!" )
    async def on_message_activity(self, turn_context: TurnContext):
        sentence = turn_context.activity.text
        
        # Acquire Response
        self.MLmodel.update_prob(sentence)

        print(f"Current state {self.Student.chatStatus}")

        print(f"User said: \"{sentence}\". gathered intent: \"{self.MLmodel.tag}\" with probability {self.MLmodel.prob.item()}")
        response = Activity(type=ActivityTypes.message)
        
        ##############################################
        # STATE : GREETING
        ##############################################
        # DESC :
        # Starting point of the user. The user can request to do a quiz, request information about their assessments, 
        ##############################################
        if self.Student.is_chat_status("greeting"):
            if not self.Student.has_spelling_errors(sentence):
                if self.MLmodel.intent_detected():
                    if self.MLmodel.is_user_intent("quiz"):
                        self.Student.set_chat_status("QuizGreeting")

                        response.text = "Welcome to the quiz menu. Here you can select a quiz for you to do:  \n  \n" +self.Student.get_student_summary() + "  \n" + " Select a quiz by entering the number in the brackets, or type quit to exit the quiz menu. "
                    
                    elif self.MLmodel.is_user_intent("quizdetails"):

                        response.text =  self.Student.get_student_summary()

                    elif self.MLmodel.is_user_intent("help"):
                        text = "You can ask me to do the following:  \n" \
                        +"'I want to do a quiz' to perform a quiz.  \n"\
                        +"'When are my quizzes due?' to check your quiz due dates.  \n"\
                        +"'Who is my course coordinator?' to see relevant staff information.  \n  \n"\
                        +"If you need assistance with your uni work, please contact your Lecturer, Tutor, HiQ, or the faculty!"
                        response.text =  text


                    else:
                        response.text = self.MLmodel.pick_response_from_model()
                else:
                    response.text = f"I do not understand....   \n  \n Type 'help' to find out what I can do or 'quit' to exit."
            else:
                response.text = f"Do you mean: " + self.Student.sentence_corrected+ "?  \nPlease re-enter your response" 

        ##############################################
        # STATE : QUIZ GREETING
        ##############################################
        # DESC :
        # User is given their available quizzes, and can select to do their desired quiz
        ##############################################
        elif self.Student.is_chat_status("QuizGreeting"):
            if self.MLmodel.intent_detected():
                if self.MLmodel.is_user_intent("quit"):
                    self.Student.set_chat_status("greeting")
                    await turn_context.send_activity("Goodbye!  \n"+ self.Student.get_student_summary())
                    response.text = f"What would you like to do?  \n  \n Type 'help' to find out what I can do or 'quit' to exit."

                else:
                    response.text = f"Not supported. Please pick a quiz or type 'quit' to return to home."
            
            elif sentence.isnumeric():
                quizName = self.Student.get_student_quiz(int(sentence))

                if quizName == -1:
                    response.text = f"That is not a valid response, pick again" 

                else: 
                    # self.Student.get_student_question()
                    await turn_context.send_activity(f"You Requested To do Quiz {quizName}")
                    response.text = self.Student.get_student_question()  + "  \n Please enter your option."
                    # response.attachments = [self._get_inline_attachment()]
                    picture = self.Student.get_question_picture()
                    if picture != -1:
                        response.attachments = [picture]
                    self.Student.set_chat_status("QuizQuestioning") #CHANGE THIS TO quizQuestioning WHEN WORKING

            else:
                response.text = f"I do not understand...." 

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
                if self.Student.has_justification_model():
                    self.Student.set_chat_status("QuizJustifying")
                    response.text = "Please Justify Your Answer" 
                else:
                    self.Student.set_chat_status("QuizConfirming")
                    self.Student.is_valid_justification_response("NA")
                    response.text = "Do you confirm? or would you like to change your answer?  \n  \nReply 'Yes' to submit answer, or 'No' to change your answer." 

            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again."

        
        ##############################################
        # STATE : QUIZ JUSTIFYING
        ##############################################
        # DESC :
        # User is asked to enter a short answer justification. 
        ##############################################
        elif self.Student.is_chat_status("QuizJustifying"):
            self.justification = sentence
            if self.Student.is_valid_justification_response(sentence) == -2: #Wrong Spelling
                response.text = "Did you mean: "+ self.Student.sentence_corrected + "?  \n  \n Reply 'Yes' to accept the corrected spelling, 'Change' to modify your answer, or 'Keep' to submit your original answer." 
                self.Student.set_chat_status("QuizSpelling")

            elif self.Student.is_valid_justification_response(sentence) == 1:
                self.Student.set_chat_status("QuizConfirming")
                response.text = "Do you confirm? or would you like to change your answer?  \n  \nReply 'Yes' to submit answer, or 'No' to change your answer."   

            
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again." 
        
        ##############################################
        # STATE : QUIZ SPELLING
        ##############################################
        # DESC :
        # User is asked to enter if . 
        ##############################################
        elif self.Student.is_chat_status("QuizSpelling"):
            self.justification = sentence
            if self.Student.is_valid_spelling_response(sentence) == 1 or self.Student.is_valid_spelling_response(sentence) == -2: #accept or keep spelling
                response.text = "Entering: "+ self.Student.new_justification 
                response.text += "  \n  \nDo you confirm? or would you like to change your answer?  \n  \nReply 'Yes' to submit answer, or 'No' to change your answer." 
                self.Student.set_chat_status("QuizConfirming")

            elif self.Student.is_valid_spelling_response(sentence) == 0:
                response.text = "Change requested. Please Enter a new response:"
                self.Student.set_chat_status("QuizJustifying")
            
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again." 
        
        ##############################################
        # STATE : QUIZ CONFIRMING
        ##############################################
        # DESC :
        # User is asked to confirm answer. They can either say yes which will submit to pointer checking, or go back to quiz questioning. 
        ##############################################
        elif self.Student.is_chat_status("QuizConfirming"):
            if self.Student.is_valid_confirm_response(sentence) == -1:
                response.text = "That is not a valid response, please enter try again." 
            
            elif self.Student.is_valid_confirm_response(sentence) == 1:# POINTER CHECKING HAPPENS HERE
                response.text = self.Student.get_feedback()
                        
                self.Student.save_progression()
                self.Student.set_chat_status("QuizFeedback")
                
            else: 
                response.text = self.Student.get_student_question()  + "  \n Please enter your option ('A', 'B', 'C', ...)"
                self.Student.set_chat_status("QuizQuestioning") 

        ##############################################
        # STATE : QUIZ FEEDBACK
        ##############################################
        # DESC :
        # User is given feedback, they can go on to do more questions or leave the quiz.
        ##############################################

        elif self.Student.is_chat_status("QuizFeedback"):
            if self.Student.is_valid_postfeedback_response(sentence) == -1:
                response.text = "That is not a valid response, please enter try again." 
            
            elif self.Student.is_valid_postfeedback_response(sentence) == 1:
                
                response.text = "Here is your next question:  \n" + self.Student.get_next_question() + "  \n Please enter your option ('A', 'B', 'C', ...)"

                picture = self.Student.get_question_picture()
                if picture != -1:
                    response.attachments = [picture]
               
                self.Student.set_chat_status("QuizQuestioning")
                
            elif self.Student.is_valid_postfeedback_response(sentence) == 0:
                self.Student.set_chat_status("QuizGreeting")

                response.text = "Welcome back to the quiz menu. Here you can select a quiz for you to do::  \n" +self.Student.get_student_summary() + "  \n" + " Select a quiz by entering the number in the brackets, or type quit to exit quiz menu. "
            #  TODO: QUIT 
            else:
                response.text = "That is not a valid response, please enter try again."

                
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


                

             
    