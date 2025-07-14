import os
from Tags import tag
from EmailHelper import email_iterator
from FileHelper import write_classification_to_file, TRUTH_FNAME, PREDICTION_FNAME
from TextHelper import word_iterator, parse_email_addr_username, parse_full_email_addr_from_str

class Corpus:
    def __init__(self, dir: str) -> None:
        self.dir = dir
        self.classification_result = {}
    
    def emails(self, load_truth=True) -> dict:
        for email_dict in email_iterator(self.dir, load_truth):
            yield email_dict
    
    def classify(self, email_name: str, classification: str) -> None:
        self.classification_result[email_name] = classification
    
    def write_classification_to_file(self) -> None:
        write_classification_to_file(self.classification_result, self.dir)
    
    def contains_truth_file(self) -> bool:
        for file in os.listdir(self.dir):
            if file == TRUTH_FNAME:
                return True
        return False
    
    def contains_prediction_file(self) -> bool:
        for file in os.listdir(self.dir):
            if file == PREDICTION_FNAME:
                return True
        return False
    
    def get_header_names(self, truth_tag:str, unique = True):
        tag_set = set()
        non_set = set()
        for email in self.emails():
            for key in email.keys():
                if email[tag.TRUTH] == truth_tag:
                    tag_set.add(key)
                else:
                    non_set.add(key)
        return tag_set - non_set if unique else tag_set.union(non_set)
    
    # for SpamDetector class
    def get_unique_header_names_of_both(self):
        spam_set = set()
        ok_set = set()
        for email in self.emails():
            for key in email.keys():
                if email[tag.TRUTH] == tag.SPAM:
                    spam_set.add(key)
                else:
                    ok_set.add(key)
        return spam_set - ok_set, ok_set - spam_set
    
    def get_addrs_from_header(self, truth_tag:str, header:str, unique = True):
        tag_set = set()
        non_set = set()
        for email in self.emails():
            if not email.get(header):
                continue
            addr = parse_full_email_addr_from_str(email[header])
            if not addr:
                continue
            # appending to correct set
            if email[tag.TRUTH] == truth_tag:
                tag_set.add(addr)
            else:
                non_set.add(addr)
        return tag_set - non_set if unique else tag_set.union(non_set)
    
    def get_unique_addrs_from_header_of_both(self, truth_tag:str, header:str, unique = True):
        spam_set = set()
        ok_set = set()
        for email in self.emails():
            if not email.get(header):
                continue
            addr = parse_full_email_addr_from_str(email[header])
            if not addr:
                continue
            # appending to correct set
            if email[tag.TRUTH] == tag.SPAM:
                spam_set.add(addr)
            else:
                ok_set.add(addr)
        return spam_set - ok_set, ok_set - spam_set
    
    def get_FROM_addr_usernames(self, truth_tag:str, unique = True):
        tag_set = set()
        non_set = set()
        for email in self.emails():
            username = parse_email_addr_username(email[tag.FROM])
            if not username:
                continue
            # appending to correct set
            if email[tag.TRUTH] == truth_tag:
                tag_set.add(username)
            else:
                non_set.add(username)
        return tag_set - non_set if unique else tag_set.union(non_set)
    
    def get_words_from_header(self, truth_tag:str, header:str, unique=True) -> set:
        tag_set = set()
        non_set = set()
        for email in self.emails():
            if email.get(header):
                for word in word_iterator(email[header]):
                    if email[tag.TRUTH] == truth_tag:
                        tag_set.add(word)
                    else:
                        non_set.add(word)
        return tag_set - non_set if unique else tag_set.union(non_set)