import json
from nltk_utils import tokenize
from nltk_utils import stem
from nltk_utils import bag_of_words
import numpy as np

import torch
import torch.nn as nn 
from torch.utils.data import Dataset, DataLoader
from model import NeuralNet
# print(intents)
with open('intents.json','r') as f:
    intents = json.load(f)
all_words = []
tags = []
xy = []
for intent in intents['intents']: #becomes a dictionary
    tag = intent['tag']
    tags.append(tag)
    
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w,tag))

ignore_words = ['?','!','.',',']
all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))

# print(tags)

X_train = []
y_train = []
for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence,all_words)
    X_train.append(bag)

    label = tags.index(tag)
    y_train.append(label) # Cross Entropy Loss

X_train = np.array(X_train)
y_train = np.array(y_train)

class ChatDataSet(): #look into python engineer beginner course where it explains it Torch Dataset
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    #dataset[idx]
    def __getitem__(self,idx):
        return self.x_data[idx], self.y_data[idx]
    
    def __len__(self):
        return self.n_samples
    

batch_size = 8
hidden_size = 8
output_size = len(tags)
input_size = len(X_train[0]) #all have same classes
learning_rate = 0.001 
num_epochs = 1000 #can try out different ones

#sanity check
# print(input_size,len(all_words))
# print(output_size,tags)

dataset = ChatDataSet()
train_loader = DataLoader(dataset = dataset, batch_size = batch_size, shuffle = True, num_workers = 0)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = NeuralNet(input_size, hidden_size, output_size).to(device)
# loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr =learning_rate)

if __name__ == '__main__':
    # Train the model
    for epoch in range(num_epochs):
        for (words, labels) in train_loader:
            words = words.to(device)
            labels = labels.to(dtype=torch.long).to(device)
            
            # Forward pass
            outputs = model(words)
            # if y would be one-hot, we must apply
            # labels = torch.max(labels, 1)[1]
            loss = criterion(outputs, labels)
            
            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
        if (epoch+1) % 100 == 0:
            print (f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')


    print(f'final loss: {loss.item():.4f}')


data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "output_size": output_size,
    "hidden_size": hidden_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "data.pth"
torch.save(data,FILE)
print(f'training complete. file saved to {FILE}')