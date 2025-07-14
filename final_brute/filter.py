from corpus import Corpus
from Tags import tag
from weights import get_weights
from ClassificationHelper import SpamDetector, get_only_ok_headers
from FileHelper import pickle_load, TRAINED_DATA_FNAME, TRAINED_DATA_DIR
import os
     
class MyFilter:
    def __init__(self) -> None:
        self.spam_detector = SpamDetector()
        self.weights = get_weights()
        self.only_ok_headers = []
        self.allow_pretrained_data = True # if pre-trained data load should be done
        self.pretrained_data_loaded = False # if load was successful
        self.trained_on_corpus = False # if filter was trained on corpus
        self.training_corpus: Corpus
        self.testing_corpus: Corpus
    
    def train(self, corpus_dir:str) -> None:
        # try to load pretrained data if allowed and not attempted before
        self.load_trained_data()
        
        # train on provided corpus
        self.training_corpus = Corpus(corpus_dir)
        self.spam_detector.train_on_corpus(self.training_corpus, self.weights)
        self.trained_on_corpus = True

        self.only_ok_headers = get_only_ok_headers(corpus_dir)
    
    def test(self, corpus_dir:str) -> None:
        # try to load pretrained data if allowed and not attempted before
        self.load_trained_data()

        self.testing_corpus = Corpus(corpus_dir)
        for email in self.testing_corpus.emails(load_truth=False):
            # getting prediction from custom class SpamDetector
            prediction = self.spam_detector.get_prediction(email, self.weights)
            # additional check that increases quality when testing yet unseen emails
            for header in email:
                if header in self.only_ok_headers:
                    prediction = tag.OK
                    break
            self.testing_corpus.classify(email[tag.NAME], prediction)
        self.testing_corpus.write_classification_to_file()
    
    # loads pre-trained data from file into memory
    def load_trained_data(self) -> None:
        # loading pre-trained data from a file
        if not self.allow_pretrained_data or self.pretrained_data_loaded:
            return
        load_file_path = os.path.join(TRAINED_DATA_DIR, TRAINED_DATA_FNAME)
        if os.path.exists(load_file_path):
            self.spam_detector = pickle_load(load_file_path)
        self.pretrained_data_loaded = True




