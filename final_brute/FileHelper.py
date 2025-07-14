import pickle, os

TRUTH_FNAME = '!truth.txt'
PREDICTION_FNAME = '!prediction.txt'
TRAINED_DATA_DIR = 'trained_data'
DEBUG_OUTPUT_DIR = 'output'
TRAINED_DATA_FNAME = 'trained_data.pickle'

# outputs classification into '!prediction.txt' from provided dict to corpus directory
def write_classification_to_file(classification: dict, corpus_dir: str) -> None:
    with open(os.path.join(corpus_dir, PREDICTION_FNAME), 'w+', encoding="utf-8") as f:
        for key in classification:
            f.write(f'{key} {classification[key]}\n')

# reads classification from provided file path (mainly for '!truth.txt') and returns data as dict
def read_classification_from_file(path:str) -> dict:
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in f.readlines():
            key, value = row.replace("\n", "").split()
            data[key] = value
    return data

# save an object to a file using pickle library
def pickle_dump(obj, fname):
    with open(fname, 'wb') as file:
        pickle.dump(obj, file)

# load an object from a file using pickle library
def pickle_load(fname):
    with open(fname, 'rb') as file:
        return pickle.load(file)
