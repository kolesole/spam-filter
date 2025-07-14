from corpus import Corpus
from Tags import tag
from weights import get_weights, weights_best2_ml, weights_best_manual
from ClassificationHelper import EmailModel, NewEmailModel, SpamDetector, get_trained_data_paths, get_only_ok_headers
from FileHelper import pprint_dump, pickle_load, pickle_dump, pprint, DEBUG_OUTPUT_DIR, TRAINED_DATA_FNAME, TRAINED_DATA_DIR
import os, random

class BaseFilter:
    def __init__(self) -> None:
        self.spam_lines = []
        self.frm = ()
        self.black_type_lst = []
        self.black_transfer_lst = []
        self.headers = ()
        self.id = ()
        self.black_headers_dic = {}

    def train(self, corpus_dir: str) -> None:
        raise NotImplementedError(self.test)

    def test(self, corpus_dir: str) -> None:
        raise NotImplementedError(self.test)
    
# Tries to classify SPAM email based on the occurence of the word "spam" in the body.
class NaiveFilter(BaseFilter):
    def test(self, corpus_dir: str) -> None:
        corpus = Corpus(corpus_dir)
        for email in corpus.emails():
            classification = "to be spam, or not to be? that is the question.."

            # ... classification logic here ...
            if "spam" in email['body'].lower():
                classification = tag.SPAM
            else:
                classification = tag.OK

            corpus.classify(email['name'], classification)
        corpus.write_classification_to_file()
        
class WordFilter(BaseFilter):
    def train(self, corpus_dir):
        f = SpamWords(corpus_dir)
        f.find_words()
        self.spam_lst = f.find_spam_words()

    def test(self, corpus_dir):
        corpus = Corpus(corpus_dir)
        for email in corpus.emails():
            for i in self.spam_lst:
                if i in email[tag.BODY]:
                    classification = tag.SPAM
                else:
                    classification = tag.OK
                corpus.classify(email[tag.NAME], classification)
        corpus.write_classification_to_file()

# Based on WordFilter logic, but more advanced
class AdvancedWordFilter(BaseFilter):
    def __init__(self) -> None:
        super().__init__()
        self.spam_email: EmailModel
        self.ok_email: EmailModel
        self.spam_email: EmailModel
        self.ok_email: EmailModel

    def train(self, corpus_dir):
        self.spam_email = EmailModel(tag.SPAM, corpus_dir)
        self.ok_email = EmailModel(tag.OK, corpus_dir)

        for key in self.spam_email.from_dns_occurences.keys():
            if key in self.ok_email.from_dns_occurences.keys():
                print(key)

        print(f'Unique SPAM word count: {len(self.spam_email.BODY_unique_words)}')
        pprint(self.spam_email.FROM_unique_domains)
        pprint(self.spam_email.from_dns_occurences)
        print(f'Unique OK word count: {len(self.ok_email.BODY_unique_words)}')
        pprint(self.ok_email.FROM_unique_domains)
        pprint(self.ok_email.from_dns_occurences)
        self.spam_email = EmailModel(tag.SPAM, corpus_dir)
        self.ok_email = EmailModel(tag.OK, corpus_dir)

        for key in self.spam_email.from_dns_occurences.keys():
            if key in self.ok_email.from_dns_occurences.keys():
                print(key)

        print(f'Unique SPAM word count: {len(self.spam_email.BODY_unique_words)}')
        pprint(self.spam_email.FROM_unique_domains)
        pprint(self.spam_email.from_dns_occurences)
        print(f'Unique OK word count: {len(self.ok_email.BODY_unique_words)}')
        pprint(self.ok_email.FROM_unique_domains)
        pprint(self.ok_email.from_dns_occurences)

    def test(self, corpus_dir):
        corpus = Corpus(corpus_dir)
        for email in corpus.emails():
            # By default, assume email is OK
            corpus.classify(email[tag.NAME], tag.OK)
            spam_est = self.spam_email.get_est_for_body(email)
            ok_est = self.ok_email.get_est_for_body(email)

            if spam_est > ok_est:
                corpus.classify(email[tag.NAME], tag.SPAM)

        corpus.write_classification_to_file()

#class StartFiltr filters emails based on a string of a certain length
class StartFilter(BaseFilter):
    def train(self, corpus_dir):
        f = SpamWords(corpus_dir)
        self.spam_lst = f.remember_lines()

    def test(self, corpus_dir):
        corpus = Corpus(corpus_dir)
        for email in corpus.emails():
            email_string = ''
            email_body = email[tag.BODY].split()
            if len(email_body) >= 30:
                for i in range(30):
                    email_string += email_body[i]
                if email_string in self.spam_lst:
                    classification = tag.SPAM
                else:
                    classification = tag.OK
            else:
                classification = tag.OK
            corpus.classify(email[tag.NAME], classification)
        corpus.write_classification_to_file()

#trial version of the filter
class SWFilter(BaseFilter):
    def train(self, corpus_dir):
        f = SpamWords(corpus_dir)
        self.spam_lst = f.remember_lines()
        self.spam_lst2 = f.find_spam_words()

    def test(self, corpus_dir):
        corpus = Corpus(corpus_dir)
        for email in corpus.emails():
            email_string = ''
            email_body = email[tag.BODY].split()
            classification = tag.OK
            if len(email_body) >= 30:
                for i in range(30):
                    email_string += email_body[i]
                if email_string in self.spam_lst2:
                    classification = tag.SPAM
                else:
                    for i in self.spam_lst:
                        if i in email_body:
                            classification = tag.SPAM
            else:
                for i in self.spam_lst:
                    if i in email_body:
                        classification = tag.SPAM
            corpus.classify(email[tag.NAME], classification)
        corpus.write_classification_to_file()

#a filter that includes the best aspects of everyone else
class BestFilter(BaseFilter):
    def train(self, corpus_dir):
        f = SpamWords(corpus_dir)
        self.spam_lines = f.remember_lines()
        self.frm = f.remember_from()
        self.black_type_lst = f.spam_content_type()
        self.black_transfer_lst = f.spam_transfer()
        self.headers = f.headers1()
        self.id = f.get_message_id_lists()

    def test(self, corpus_dir):
        corpus = Corpus(corpus_dir)
        for email in corpus.emails():
            if email[tag.FROM].lower() in self.frm[1] or (tag.MESSAGE_ID in email and email[tag.MESSAGE_ID].lower() in self.id[1]):
                classification = tag.OK
            elif (tag.CONTENT_TYPE in email and email[tag.CONTENT_TYPE].lower() in self.black_type_lst) or\
                    (tag.CONTENT_TRANSFER_ENCODING in email and email[tag.CONTENT_TRANSFER_ENCODING].lower() in self.black_transfer_lst) or \
                    email[tag.FROM].lower() in self.frm[0] or (tag.MESSAGE_ID in email and email[tag.MESSAGE_ID].lower() in self.id[0]):
                classification = tag.SPAM
            else:
                email_string = ''
                email_body = email[tag.BODY].split()
                if len(email_body) >= 3:
                    for i in range(3):
                        email_string += email_body[i]
                    if email_string.lower() in self.spam_lines:
                        classification = tag.SPAM
                    else:
                        classification = tag.OK
                else:
                    classification = tag.OK
            for i in email:
                if i.lower() in self.headers[0]:
                    classification = tag.SPAM
                    break
                elif i.lower() in self.headers[1]:
                    classification = tag.OK
                    break
            corpus.classify(email[tag.NAME], classification)
        corpus.write_classification_to_file()

class WonderfulFilter(BaseFilter):
    def train(self, corpus_dir):
        f = SpamWords(corpus_dir)
        self.black_headers_dic = f.spam_headers_body()
        # self.ok_headers_dic = f.spam_headers_body()[1]
        self.headers = f.headers1()
        # if 'data/1' in corpus_dir:
        #     f = open('black_headers_dic_data1.txt', 'a+', encoding='utf-8')
        #     for i in self.black_headers_dic:
        #         f.write(i + ' ' + str(self.black_headers_dic[i]) + '\n')
        #     f.close()
        # elif 'data/2' in corpus_dir:
        #     f = open('ok_headers_dic_data2.txt', 'a+', encoding='utf-8')
        #     for i in self.ok_headers_dic:
        #         f.write(i + ' ' + str(self.black_headers_dic[i]) + '\n')
        #     f.close()


    def test(self, corpus_dir):
        corpus = Corpus(corpus_dir)
        for email in corpus.emails(load_truth=False):
            classification = tag.OK
            for header in email:
                if header.lower() in self.black_headers_dic and email[header].lower() in self.black_headers_dic[header.lower()]:
                    classification = tag.SPAM
                    break
            for header in email:
                if header.lower() in self.headers[1]:
                    classification = tag.OK
                    break
            corpus.classify(email[tag.NAME], classification)
        corpus.write_classification_to_file()

# inspired by all previous filter iterations
class MultiMethodFilter(BaseFilter):
    def __init__(self) -> None:
        super().__init__()
        self.spam_model: EmailModel
        self.ok_model: EmailModel
        self.weights = {tag.FROM: 0.25, 
                        tag.BODY: 0.56, 
                        tag.SUBJECT: 0.06,
                        tag.HEADER_NAMES: 0.05}

    def train(self, corpus_dir):
        self.spam_model = EmailModel(tag.SPAM, corpus_dir, self.weights)
        self.ok_model = EmailModel(tag.OK, corpus_dir, self.weights)
    
    def test(self, corpus_dir: str, weights:dict = None) -> None:
        if weights:
            self.weights = weights
        corpus = Corpus(corpus_dir)
        for email in corpus.emails(load_truth=False):
            pprint_dump(email, os.path.join(DEBUG_OUTPUT_DIR, email[tag.NAME]))
            prob_spam = self.spam_model.get_probability_for_email(email, self.weights)
            prob_ok = self.ok_model.get_probability_for_email(email, self.weights)
            if prob_spam > prob_ok:
                corpus.classify(email[tag.NAME], tag.SPAM)
            else:
                corpus.classify(email[tag.NAME], tag.OK)
        corpus.write_classification_to_file()

class TrainedFilter(BaseFilter):
    def __init__(self, allow_pretrained_data = False) -> None:
        self.model_spam = NewEmailModel(tag.SPAM)
        self.model_ok = NewEmailModel(tag.OK)
        self.weights = weights_best_manual
        self.allow_pretrained_data = allow_pretrained_data # if load should be done
        self.pretrained_data_loaded = False # if load was successful
        self.pretrained_data_load_attempt = False # if load was attempted
        self.trained_on_corpus = False # if filter was trained on corpus
        self.training_corpus: Corpus
        self.testing_corpus: Corpus

    def train(self, corpus_dir:str) -> None:
        # try to load pretrained data if allowed and not tried before
        self.load_trained_data()
        
        # train on provided corpus
        self.training_corpus = Corpus(corpus_dir)
        self.model_spam.train_on_corpus(self.training_corpus, self.weights)
        self.model_ok.train_on_corpus(self.training_corpus, self.weights)
        self.trained_on_corpus = True
    
    def test(self, corpus_dir:str, weights:dict = None) -> None:
        # to allow training.py pre-training filters
        if weights:
            self.weights = weights
        
        # try to load pretrained data if allowed and not tried before
        self.load_trained_data()

        if False and not any((self.trained_on_corpus, self.pretrained_data_loaded)):
            raise BaseException("Unable to test using untrained filter")

        self.testing_corpus = Corpus(corpus_dir)
        for email in self.testing_corpus.emails(load_truth=False):
            if not os.path.exists(DEBUG_OUTPUT_DIR):
                os.mkdir(DEBUG_OUTPUT_DIR)
            pprint_dump(email, os.path.join(DEBUG_OUTPUT_DIR, email[tag.NAME]))
            prob_spam = self.model_spam.get_prob_for_email(email, self.weights)
            prob_ok = self.model_ok.get_prob_for_email(email, self.weights)
            prediction = tag.SPAM if prob_spam > prob_ok else tag.OK
            self.testing_corpus.classify(email[tag.NAME], prediction)
        self.testing_corpus.write_classification_to_file()

    def load_trained_data(self, dir = 'trained_data') -> None:
        if not self.allow_pretrained_data or self.pretrained_data_load_attempt or self.pretrained_data_loaded:
            return
        model_ok_loaded = False
        model_spam_loaded = False
        for model_path in get_trained_data_paths(dir):
            if model_path.endswith(tag.OK):
                self.model_ok.merge_trained_data_dict(pickle_load(model_path))
                model_ok_loaded = True
            elif model_path.endswith(tag.SPAM):
                self.model_spam.merge_trained_data_dict(pickle_load(model_path))
                model_spam_loaded = True
        self.pretrained_data_load_attempt = True
        self.pretrained_data_loaded = model_ok_loaded and model_spam_loaded
    
    def dump_trained_data(self, dir = 'trained_data', use_pprint = False):
        for model in (self.model_ok, self.model_spam):
            dump_func = pprint_dump if use_pprint else pickle_dump
            dump_func(model.trained_data, os.path.join(dir, 'model' + model.truth_tag))

    def trained_data_filename(self) -> str:
        pass
        
class MultiWonderfulFilter(BaseFilter):

    def __init__(self) -> None:
        super().__init__()
        self.spam_model: EmailModel
        self.ok_model: EmailModel
        self.weights = {tag.FROM: 0.25,
                        tag.BODY: 0.56,
                        tag.SUBJECT: 0.06,
                        tag.HEADER_NAMES: 0.05}

    def train(self, corpus_dir):
        f = SpamWords(corpus_dir)
        self.black_headers_dic = f.spam_headers_body()
        self.ok_headers_dic = f.ok_headers_body()
        self.headers = f.headers1()
        self.spam_model = EmailModel(tag.SPAM, corpus_dir, self.weights)
        self.ok_model = EmailModel(tag.OK, corpus_dir, self.weights)

    def test(self, corpus_dir: str, weights: dict = None) -> None:
        if weights:
            self.weights = weights
        corpus = Corpus(corpus_dir)
        for email in corpus.emails(load_truth=False):
            #pprint_dump(email, 'output/' + email[tag.NAME])
            prob_spam = self.spam_model.get_probability_for_email(email, self.weights)
            prob_ok = self.ok_model.get_probability_for_email(email, self.weights)
            classification = tag.OK
            for header in email:
                if header.lower() in self.black_headers_dic and email[header].lower() in self.black_headers_dic[
                    header.lower()]:
                    classification = tag.SPAM
                    break
            if prob_spam > prob_ok:
                classification = tag.SPAM
                for header in email:
                    if header.lower() in self.headers[1]:
                        classification = tag.OK
                        break
                corpus.classify(email[tag.NAME], classification)
            corpus.write_classification_to_file()
        
class OptimizedTrainedFilter(BaseFilter):
    def __init__(self, allow_pretrained_data = False) -> None:
        self.spam_detector = SpamDetector()
        self.weights = get_weights()
        self.allow_pretrained_data = allow_pretrained_data # if load should be done
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

    def test(self, corpus_dir:str, weights:dict = None) -> None:
        # to allow training.py pre-training filters
        if weights:
            self.weights = weights
        
        # try to load pretrained data if allowed and not attempted before
        self.load_trained_data()

        self.testing_corpus = Corpus(corpus_dir)
        for email in self.testing_corpus.emails(load_truth=False):
            prediction = self.spam_detector.get_prediction(email, self.weights)
            self.testing_corpus.classify(email[tag.NAME], prediction)
        self.testing_corpus.write_classification_to_file()
    
    def load_trained_data(self) -> None:
        if not self.allow_pretrained_data or self.pretrained_data_loaded:
            return
        load_file_path = os.path.join(TRAINED_DATA_DIR, TRAINED_DATA_FNAME)
        if os.path.exists(load_file_path):
            self.spam_detector = pickle_load(load_file_path)
        self.pretrained_data_loaded = True
        
    def dump_trained_data(self) -> None:
        load_file_path = os.path.join(TRAINED_DATA_DIR, TRAINED_DATA_FNAME)
        pickle_dump(self.spam_detector, load_file_path)

class MyFilter(OptimizedTrainedFilter):
    pass



