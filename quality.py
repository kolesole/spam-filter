import os
from Tags import tag
from confmat import BinaryConfusionMatrix
from FileHelper import read_classification_from_file, TRUTH_FNAME, PREDICTION_FNAME

def get_confmat_dict(corpus_dir, print_fp = False) -> dict:
    # Paths validation
    truth_path = os.path.join(corpus_dir, TRUTH_FNAME)
    prediction_path = os.path.join(corpus_dir, PREDICTION_FNAME)
    for path in (corpus_dir, truth_path, prediction_path):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
    
    # reading and evaluating classification data
    truth_dict = read_classification_from_file(truth_path)
    prediction_dict = read_classification_from_file(prediction_path)
    if print_fp:
        for email in truth_dict.keys():
            if prediction_dict[email] != truth_dict[email] and truth_dict[email] == tag.OK:
                print("Misclassf as SPAM: output/" + email)
    confmat = BinaryConfusionMatrix(pos_tag=tag.SPAM, neg_tag=tag.OK)
    confmat.compute_from_dicts(truth_dict, prediction_dict)
    return confmat.as_dict()

def quality_score(tp:int, tn:int, fp:int, fn:int) -> float:
    return (tp + tn) / (tp + tn + 10*fp + fn)

def compute_quality_for_corpus(corpus_dir: str, print_fp = False) -> float:
    confmat_dict = get_confmat_dict(corpus_dir, print_fp)
    return quality_score(tp=confmat_dict["tp"], 
                         tn=confmat_dict["tn"], 
                         fp=confmat_dict["fp"], 
                         fn=confmat_dict["fn"])
    