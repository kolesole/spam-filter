import os
from Tags import tag, HEADERS_CONTAINING_EMAIL_ADDRESSES
from EmailHelper import email_iterator
from FileHelper import pickle_load, read_classification_from_file
from TextHelper import word_iterator, parse_full_email_addr_from_str, parse_email_addr_username, spam_keywords
from corpus import Corpus

class EmailModel:
    def __init__(self, truth_tag:str, corpus_dir:str, weights:dict, load_data_from_cwd = False) -> None:
        self.truth_tag = truth_tag  # SPAM or OK
        self.corpus_dir = corpus_dir
        self.weights = weights
        self.load_data_from_cwd = load_data_from_cwd
        self.unique_elems = {}
        self.train()
    
    def train(self):
        # retrieve trained parsed data from cwd if allowed and available;
        local_data = self.get_trained_data_file_path()
        if self.load_data_from_cwd and os.path.exists(local_data):
            self.unique_elems = pickle_load(local_data)
        
        # train on newly provided unparsed data from corpus.
        # handling of specific tag cases, otherwise use word iterator as fallback
        for key in self.weights.keys():
            match key:
                case tag.HEADER_NAMES:
                    self.add_trained_data(self.get_unique_keys(), key)
                case tag.FROM:
                    self.add_trained_data(self.get_unique_FROM_usernames(), key)
                case _:
                    self.add_trained_data(self.get_unique_words_by_tag(key), key)

    # helper func to add trained data to own dataset without erasing current data        
    def add_trained_data(self, data:set, tag:str) -> None:
        if tag in self.unique_elems.keys():
            self.unique_elems[tag] = self.unique_elems[tag].union(data)
        else:
            self.unique_elems[tag] = data
    
    def get_trained_data_file_path(self):
        return '_'.join((self.truth_tag, "training_data"))
    
    def get_unique_words_by_tag(self, header:str) -> set:
        tag_words = set()
        other_words = set()
        for email in email_iterator(self.corpus_dir):
            if email.get(header):
                for word in word_iterator(email[header]):
                    if email[tag.TRUTH] == self.truth_tag:
                        tag_words.add(word)
                    else:
                        other_words.add(word)
        return tag_words - other_words
    
    def get_unique_FROM_usernames(self):
        tag_uns = set()
        other_uns = set()
        for email in email_iterator(self.corpus_dir):
            username = parse_email_addr_username(email[tag.FROM])
            if not username:
                continue
            # appending to correct set
            if email[tag.TRUTH] == self.truth_tag:
                tag_uns.add(username)
            else:
                other_uns.add(username)
        return tag_uns - other_uns

    def get_unique_keys(self, all = False):
        tag_keys = set()
        other_keys = set()
        for email in email_iterator(self.corpus_dir):
            for key in email.keys():
                if email[tag.TRUTH] == self.truth_tag:
                    tag_keys.add(key)
                else:
                    other_keys.add(key)
        if all:
            return tag_keys.union(other_keys)
        else:
            return tag_keys - other_keys
        
    def get_probability_for_email(self, email:dict, weights:dict = None) -> float:
        # probabilities container
        probs = get_zeroed_weights_dict(weights)

        # _norm_count works like .count(elem), but for any two iterables and returns normalized value.
        # Ex: _norm_count([2, 4], [1, 2, 3, 4]) = 0.5
        _norm_count = lambda iter_sub, iter_all : sum(1 for elem in iter_sub if elem in iter_all) / len(iter_all)
        _int_contains = lambda elem, iter : 1 if elem in iter else 0
        _contains_alnum = lambda text : any(char.isalnum() for char in text)
        
        # early probability for each data target, if data are available
        for header in probs.keys():
            if header == tag.HEADER_NAMES and self.unique_elems.get(header):
                probs[header] = _norm_count(email.keys(), self.unique_elems[header])
            elif header == tag.FROM:
                username = parse_email_addr_username(email[tag.FROM])
                if self.unique_elems.get(header) and username:
                    probs[header] = _int_contains(username, self.unique_elems[header])
            elif email.get(header) and self.unique_elems.get(header):
                probs[header] = _norm_count(word_iterator(email[header]), self.unique_elems[header])
        
        # calculating final probability based on predifined weights:
        return calc_dict_dot_product(probs, weights if weights else self.weights)

class NewEmailModel:
    def __init__(self, truth_tag:str) -> None:
        self.truth_tag = truth_tag  # SPAM or OK
        self.trained_data = {}
    
    def merge_trained_data_dict(self, new_trained_data:dict) -> None:
        for header in new_trained_data.keys():
            self.merge_trained_data_set(new_trained_data[header], header)
    
    def merge_trained_data_set(self, new_trained_data:set, header:str) -> None:
        if not header in self.trained_data.keys():
            self.trained_data[header] = new_trained_data
        else:
            self.trained_data[header] = self.trained_data[header].union(new_trained_data)
        
    def train_on_corpus(self, corpus: Corpus, weights:dict) -> None:        
        # train on newly provided corpus.
        # handling of specific tag cases, otherwise use word iterator as fallback
        for header in weights.keys():
            if header == tag.HEADER_NAMES:
                self.merge_trained_data_set(corpus.get_header_names(self.truth_tag), header)
            elif header in HEADERS_CONTAINING_EMAIL_ADDRESSES:
                self.merge_trained_data_set(corpus.get_addrs_from_header(self.truth_tag, header), header)
            else:
                self.merge_trained_data_set(corpus.get_words_from_header(self.truth_tag, header), header)
    
    def get_prob_for_email(self, email:dict, weights:dict = None) -> float:
        # probabilities container
        probs = get_zeroed_weights_dict(weights)
        
        # early probability for each data target, if data are available
        for key in probs.keys():
            # checking for suspicious header names
            if key == tag.HEADER_NAMES and self.trained_data.get(key):
                probs[key] = norm_count(email.keys(), self.trained_data[key])
            # checking for suspicious words in some headers
            elif key == tag.COMMON_SPAM_WORDS:
                if not self.truth_tag == tag.SPAM:
                    continue
                words_to_check = ' '.join(email[h] for h in (tag.BODY, tag.SUBJECT)).split()
                if words_to_check:
                    probs[key] = norm_count(spam_keywords, words_to_check)
            elif key in HEADERS_CONTAINING_EMAIL_ADDRESSES:
                addr = parse_full_email_addr_from_str(email[tag.FROM])
                if self.trained_data.get(key) and addr:
                    probs[key] = int(addr in self.trained_data[key])
            elif email.get(key) and self.trained_data.get(key):
                probs[key] = norm_count(word_iterator(email[key]), self.trained_data[key])

        # calculating final probability based on predifined weights:
        return calc_dict_dot_product(probs, weights)

class SpamDetector:
    def __init__(self) -> None:
        self.spam_data = {}
        self.ok_data = {}

    def merge_trained_data_dict(self, data_tag:str, new_trained_data:dict) -> None:
        for header in new_trained_data.keys():
            self.merge_trained_data_set(data_tag, new_trained_data[header], header)
    
    def merge_trained_data_set(self, data_tag:str, new_trained_data:set, header:str) -> None:
        trained_data = self.spam_data if data_tag == tag.SPAM else self.ok_data
        if not header in trained_data.keys():
            trained_data[header] = set(new_trained_data)
        else:
            trained_data[header] = trained_data[header].union(new_trained_data)
    
    def train_on_corpus(self, corpus: Corpus, weights:dict) -> None:        
        # collecting text data from training corpus emails
        spam_dict = {key: set() for key in weights.keys()}
        ok_dict = {key: set() for key in weights.keys()}
        for email in corpus.emails():
            target_dict = spam_dict if email[tag.TRUTH] == tag.SPAM else ok_dict
            for header in weights.keys():

                # --- Email headers parsing ---
                if header == tag.HEADER_NAMES:
                    target_dict[header] = target_dict[header].union(email.keys())
                    
                if header not in email.keys():
                    continue
                
                # --- Email addresses parsing from within headers ---
                elif header in HEADERS_CONTAINING_EMAIL_ADDRESSES:
                    addr = parse_full_email_addr_from_str(email[header])
                    if addr: target_dict[header].add(addr)
                
                # --- regular word parsing ---
                else:
                    target_dict[header] = target_dict[header].union(word_iterator(email[header]))
        
        # inserting unique text entries into model memory
        for header in weights.keys():
            self.merge_trained_data_set(tag.SPAM, spam_dict[header] - ok_dict[header], header)
            self.merge_trained_data_set(tag.OK, ok_dict[header] - spam_dict[header], header)

    def get_prediction(self, email:dict, weights:dict) -> str:
        # probabilities containers
        probs_spam = {key: 0 for key in weights.keys()}
        probs_ok = {key: 0 for key in weights.keys()}
        data_available = lambda key: bool(self.spam_data.get(key) and self.ok_data.get(key))

        # early probability for each data target, if data are available
        for key in weights.keys():

            # somehow, checking for unique headers as strict determinant raises quality
            if key == tag.HEADER_NAMES:
                if self.ok_data[tag.HEADER_NAMES].intersection(email.keys()):
                    probs_ok[key] = 1

            # checking for suspicious words in some headers
            elif key == tag.COMMON_SPAM_WORDS:
                tags_to_check = (tag.BODY, tag.SUBJECT)
                words_to_check = ' '.join(email[h] for h in tags_to_check if email.get(h)).split()
                if words_to_check:
                    probs_spam[key] = norm_count(spam_keywords, words_to_check)
            
            # the rest of checks are based on header key
            elif not key in email.keys():
                continue

            # checking known email adresses
            elif key in HEADERS_CONTAINING_EMAIL_ADDRESSES:
                addr = parse_full_email_addr_from_str(email[key])
                if addr:
                    probs_spam[key] = int(addr in self.spam_data[key])
                    probs_ok[key] = int(addr in self.ok_data[key])
            
            # checking any other key based on words only
            else:
                probs_spam[key] = norm_count(word_iterator(email[key]), self.spam_data[key])
                probs_ok[key] = norm_count(word_iterator(email[key]), self.ok_data[key])

        # calculating and returning final probability based on predifined weights:
        probability_of_spam = calc_dict_dot_product(probs_spam, weights)
        probability_of_ok = calc_dict_dot_product(probs_ok, weights)
        return tag.SPAM if probability_of_spam > probability_of_ok else tag.OK

def norm_count(iter_sub, iter_all) -> float:
    if len(iter_all) == 0:
        return 0
    return sum(1 for elem in iter_sub if elem in iter_all) / len(iter_all)

def count_classifications_from_file(path:str) -> dict:
    counts = {
        tag.SPAM: 0,
        tag.OK: 0
    }

    for classification in read_classification_from_file(path).values():
        match classification:
            case tag.SPAM:
                counts[tag.SPAM] += 1
            case tag.OK:
                counts[tag.OK] += 1
            case _:
                raise ValueError(f"Invalid clasification string '{classification}' encountered.")
    return counts

def normalize_dict(dct:dict) -> dict:
    normalized_dict = {}
    sum_of_values = sum(v for v in dct.values())
    for key, value in dct.items():
        normalized_dict[key] = value / sum_of_values
    return normalized_dict

def calc_dict_dot_product(dict1:dict, dict2:dict) -> float:
    if dict1.keys() != dict2.keys():
        raise ValueError(f"Cannot multiply following dicts due to having different keys:\n{dict1}\n{dict2}")
    return sum(val*dict2[key] for key, val in dict1.items())

def get_zeroed_weights_dict(weights:dict):
    return {key: 0 for key in weights.keys()}

def get_trained_data_paths(trained_data_dir) -> str:
    for filename in os.listdir(trained_data_dir):
        if filename.endswith(tag.SPAM) or filename.endswith(tag.OK):
            yield os.path.join(trained_data_dir, filename)

# function returns a list with the headers og only ok emails
def get_only_ok_headers(path):
    ok_headers = []
    spam_headers = []
    only_ok_headers = []
    for email in email_iterator(path):
        for header in email:
            if email[tag.TRUTH] == tag.SPAM and header not in spam_headers:
                spam_headers.append(header)
            elif email[tag.TRUTH] == tag.OK and header not in ok_headers:
                ok_headers.append(header)
    for header in ok_headers:
        if header not in spam_headers:
            only_ok_headers.append(header)
    return only_ok_headers



            
        
        