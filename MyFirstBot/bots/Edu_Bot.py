# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import random
import json
import torch
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
                    response = f"That is not a valid response, pick again"
                else:
                    # self.Student.get_student_question()
                    await turn_context.send_activity(f"You Requested To do Quiz {quizName}")
                    response = self.Student.get_student_question()  + "  \n Please enter your option."
                    self.Student.chatStatus = "QuizQuestioning" #CHANGE THIS TO quizQuestioning WHEN WORKING

            else:
                response = f"I do not understand...."



        elif  self.Student.is_chat_status("QuizQuestioning"):
            # send details when you get into quiz as an await.
            if self.Student.check_correct_answer(sentence):
                response = "Correct"
            else:
                response = "Wrong"
            

                
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


                

             
    