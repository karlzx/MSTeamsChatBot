
import pickle
import numpy as np
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

if __name__ == "__main__":

    #Export vocab for each question before looking
    #exportQ1Vocab()

    #Create model for each question
    #createQ1Model()

    #Test some example setences prediction
    sentence1 = 'Frequency is the inverse of period' #Should be 1
    sentence2 = 'guess' #Should be 3
    sentence3 = 'Random words I am typing' #Should be 3
    sentence4 = 'The amplitude is higher' #Should be 3
    sentence5 = 'Option (a) has the greatest frequency, as the cycles oscillate the most.'  # Should be 3
    sentence6 = 'The signal frequency amplitude period is the highest in time.'
    sentence7 = 'The amplitude is the largest'
    
    out1 = predQ1Model(sentence1)
    out2 = predQ1Model(sentence2)
    # out3 = predQ1Model(sentence3)
    out4 = predQ1Model(sentence4)
    out5 = predQ1Model(sentence5)
    out6 = predQ1Model(sentence6)
    out7 = predQ1Model(sentence7)

    
    print("For input " + sentence1)
    print("The result is: " + out1)

    
    print("For input " + sentence2)
    print("The result is: " + out2)

    print("For input " + sentence5)
    print("The result is: " + out5)
    print("For input " + sentence4)
    print("The result is: " + out4)
    print('done')


