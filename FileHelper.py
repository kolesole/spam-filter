import pickle, os
from pprint import pprint

TRUTH_FNAME = '!truth.txt'
PREDICTION_FNAME = '!prediction.txt'
CORPUS_ROOT_DIR = 'data'
TRAINED_DATA_DIR = 'trained_data'
DEBUG_OUTPUT_DIR = 'output'
TRAINED_DATA_FNAME = 'trained_data.pickle'
CORPUS_LIST = [os.path.join(CORPUS_ROOT_DIR, corpus) for corpus in os.listdir(CORPUS_ROOT_DIR) if corpus != 'c']

def write_classification_to_file(classification: dict, corpus_dir: str) -> None:
    with open(os.path.join(corpus_dir, PREDICTION_FNAME), 'w+', encoding="utf-8") as f:
        for key in classification:
            f.write(f'{key} {classification[key]}\n')

def read_classification_from_file(path:str) -> dict:
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in f.readlines():
            key, value = row.replace("\n", "").split()
            data[key] = value
    return data 

def pickle_dump(obj, fname):
    """Save an object to a file using pickle."""
    with open(fname, 'wb') as file:
        pickle.dump(obj, file)

def pickle_load(fname):
    """Load an object from a file using pickle."""
    with open(fname, 'rb') as file:
        return pickle.load(file)

def pprint_dump(obj, fname):
    with open(fname, 'w', encoding='utf-8') as f:
        pprint(obj, f)