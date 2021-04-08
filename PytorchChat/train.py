import json
from nltk_utils import tokenize
from nltk_utils import stem
import numpy as np
with open('intents.json','r') as f:
    intents = json.load(f)

import torch
import torch.nn as nn 
from torch.utils.data import Dataset, DataLoader

# print(intents)

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

print(tags)

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
        self.ydata = y_train

    #dataset[idx]
    def __getitem__(self,idx):
        return self.x_data[idx], self.y_data[idx]
    
    def __len__(self):
        return self.n_samples
    
    batch_size = 8
    dataset = ChatDataSet()
    train_loader = DataLoader(dataset = dataset, batch_size = batch_size, shuffle = True, num_workers = 2)