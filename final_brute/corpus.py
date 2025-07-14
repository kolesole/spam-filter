from EmailHelper import email_iterator
from FileHelper import write_classification_to_file

class Corpus:
    def __init__(self, dir: str) -> None:
        self.dir = dir
        self.classification_result = {}
    
    # email iterator
    def emails(self, load_truth=True) -> dict:
        for email_dict in email_iterator(self.dir, load_truth):
            yield email_dict
    
    # saves classification of individual emails into memory
    def classify(self, email_name: str, classification: str) -> None:
        self.classification_result[email_name] = classification
    
    # writes saved classification to a file '!prediction.txt'
    def write_classification_to_file(self) -> None:
        write_classification_to_file(self.classification_result, self.dir)
        