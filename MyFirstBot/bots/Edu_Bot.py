# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import random
import json
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount


class EduBot(ActivityHandler):
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        with open('intents.json','r') as f:
            self.intents = json.load(f)

        FILE = "data.pth"

        data = torch.load(FILE)

        self.input_size = data["input_size"]
        self.hidden_size = data["hidden_size"]
        self.output_size = data["output_size"]
        self.all_words = data["all_words"]
        self.tags = data["tags"]
        self.model_state = data["model_state"]


        self.model = NeuralNet( self.input_size,  self.hidden_size,  self.output_size).to( self.device)
        self.model.load_state_dict( self.model_state)
        self.model.eval()

        self.bot_name = "Ed"

        self.status = "start"

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hi I'm Ed the Educational Bot! type 'quit' to exit")

    async def on_message_activity(self, turn_context: TurnContext):
        sentence = turn_context.activity.text

        sentence = tokenize(sentence)
        X = bag_of_words(sentence, self.all_words)
        X = X.reshape(1,X.shape[0])
        X = torch.from_numpy(X).to(self.device)
        output = self.model(X)
        _,predicted = torch.max(output, dim=1)

        tag = self.tags[predicted.item()]

        probs = torch.softmax(output, dim = 1)
        prob = probs[0][predicted.item()]
        acceptance_probability = 0.75

        print(f"Current state {self.status}")

        print(f"User said {sentence}. gathered: intent {tag} with probability {prob.item()}")

        if self.status == "start":
            if prob.item() > acceptance_probability:
                for intent in self.intents["intents"]:
                    if tag == intent["tag"]:
                        response = f"{random.choice(intent['responses'])}" 
                    if tag == "quiz":
                        self.status = "quizquestioned"
            else:
                    response = f"I do not understand...."
        
        elif self.status == "quizquestioned":
            if prob.item() > acceptance_probability:
                if tag == "yes":
                    response = f"Starting the quiz... "
                    self.status = "quiz"

                else:
                    response = f"No worries! What would you like to do?"
                    self.status == "start"

            else:
                    response = f"I do not understand...."
        
        elif self.status == "quiz":
            response = f"You are now in quiz mode"

            if prob.item() > acceptance_probability:
                if tag == "quit":
                    response = f"Taking you back"
                    self.status = "start"
                

             

        return await turn_context.send_activity(
            MessageFactory.text(f"{response}")
        )
