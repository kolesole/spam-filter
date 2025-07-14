from Tags import tag, HEADERS_CONTAINING_EMAIL_ADDRESSES
from EmailHelper import email_iterator
from TextHelper import word_iterator, parse_full_email_addr_from_str, spam_keywords
from corpus import Corpus

class SpamDetector:
    def __init__(self) -> None:
        self.spam_data = {}
        self.ok_data = {}

    def merge_trained_data_set(self, truth_tag: str, new_trained_data: set, header: str) -> None:
        trained_data = self.spam_data if truth_tag == tag.SPAM else self.ok_data
        if not header in trained_data.keys():
            trained_data[header] = set(new_trained_data)
        else:
            trained_data[header] = trained_data[header].union(new_trained_data)

    def train_on_corpus(self, corpus: Corpus, weights: dict) -> None:
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

    def get_prediction(self, email: dict, weights: dict) -> str:
        # probabilities containers
        probs_spam = {key: 0 for key in weights.keys()}
        probs_ok = {key: 0 for key in weights.keys()}

        # early probability for each data target, if data are available
        for key in weights.keys():

            # checking for suspicious header names
            if key == tag.HEADER_NAMES:
                probs_spam[key] = norm_count(email.keys(), self.spam_data[key])
                probs_ok[key] = norm_count(email.keys(), self.ok_data[key])

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

# returns normalized occurence rate of elements from one iterable (iter_sub) in other iterable (iter_all)
def norm_count(iter_sub, iter_all) -> float:
    if len(iter_all) == 0:
        return 0
    return sum(1 for elem in iter_sub if elem in iter_all) / len(iter_all)

# calculates dot product of two vectors as dicts where values are ints or floats. dicts must have equal keys.
def calc_dict_dot_product(dict1: dict, dict2: dict) -> float:
    if dict1.keys() != dict2.keys():
        raise ValueError(f"Cannot multiply following dicts due to having different keys:\n{dict1}\n{dict2}")
    return sum(val * dict2[key] for key, val in dict1.items())

# function returns a list with the headers of only ok emails
def get_only_ok_headers(path) -> list:
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
