import sys, os
from Tags import tag
from filter import MyFilter
from quality import compute_quality_for_corpus, get_confmat_dict
from ClassificationHelper import count_classifications_from_file
from FileHelper import TRUTH_FNAME, PREDICTION_FNAME, CORPUS_LIST
from itertools import product
from datetime import datetime

command_line_args = {
    'del_output': False,  # If True, deletes output files '!prediction.txt' after execution.
    'corpus_rep_off': False, # If True, doesn't train and test on the same corpus
    'short': False, # if True, prints only short version of output
    'skip_train': False, # If true, training is skipped.
    'print_fp': False, # If true, prints missclassified FalsePos email warnings.
    'allow_pretrained_data': False # If true, loads filter with pre-trained data
}

def main() -> None:
    # printing weight values if filter utilizes them
    first_weight_line = True
    temp = MyFilter()
    if 'weights' in temp.__dict__.keys() and not command_line_args['short']:
        for key, value in temp.weights.items():
            if first_weight_line:
                print(f'Weights:    {key}: {value}')
                first_weight_line = False
            else:
                print(f'            {key}: {value}')
        print('-'*30)
    
    quality_outputs = []

    # filter testing
    for train_corpus, test_corpus in product(CORPUS_LIST, repeat=2):
        if command_line_args['corpus_rep_off'] and (train_corpus == test_corpus or 'data/c' in (train_corpus, test_corpus)):
            continue
        
        truth_file_path_test_corp = os.path.join(test_corpus, TRUTH_FNAME)
        truth_file_path_train_corp = os.path.join(train_corpus, TRUTH_FNAME)
        pred_file_path_test_corp = os.path.join(test_corpus, PREDICTION_FNAME)
        temp_truth_file_path_test_corp = os.path.join(test_corpus, '!' + TRUTH_FNAME)
        temp_truth_file_path_train_corp = os.path.join(train_corpus, '!' + TRUTH_FNAME)

        # if previous run didn't rename truth file back, rename it now
        if os.path.exists(temp_truth_file_path_train_corp):
            os.rename(temp_truth_file_path_train_corp, truth_file_path_train_corp)

        # deleting !prediction.txt from test_corpus
        if os.path.exists(pred_file_path_test_corp):
            os.remove(pred_file_path_test_corp)

        # Creating and training filter
        f = MyFilter(command_line_args['allow_pretrained_data'])
        train_time_start = datetime.now()
        if not command_line_args['skip_train']:
            f.train(train_corpus)
        train_time_end = datetime.now()
        
        # if !truth.txt is present in test_corpus, rename it temporarily
        if os.path.exists(truth_file_path_test_corp):
            os.rename(truth_file_path_test_corp, temp_truth_file_path_test_corp)

        # testing filter
        test_time_start = datetime.now()
        f.test(test_corpus)
        test_time_end = datetime.now()

        # move back truth file to test_corpus
        if os.path.exists(temp_truth_file_path_test_corp):
            os.rename(temp_truth_file_path_test_corp, truth_file_path_test_corp)

        # assembling info
        quality = compute_quality_for_corpus(test_corpus, command_line_args['print_fp'])
        quality_outputs.append(quality)
        predict_counts = count_classifications_from_file(pred_file_path_test_corp)
        truth_counts = count_classifications_from_file(truth_file_path_test_corp)
        train_duration = round((train_time_end - train_time_start).total_seconds(), ndigits=2)
        test_duration = round((test_time_end - test_time_start).total_seconds(), ndigits=2)
        confmat = get_confmat_dict(test_corpus)

        # printing info
        if command_line_args['short']:
            print(f'{train_corpus} -> {test_corpus}: {round(quality*100, 2)}% ({quality})')
            continue
        print(f'Filter:         {getInheritanceHierarchy(f)}')
        if command_line_args['skip_train']:
            print(f'Trained on:     Training was skipped.')
        else:
            print(f'Trained on:     {train_corpus} ({train_duration} seconds)')
        if train_duration > 5*60: print("Warning! Training took longer than BRUTE accepts (5 minutes)")
        print(f'Tested on:      {test_corpus} ({test_duration} seconds)')
        if test_duration > 2*60: print("Warning! Testing took longer than BRUTE accepts (2 minutes)")
        print(f'Spam count:     {predict_counts[tag.SPAM]} (truth: {truth_counts[tag.SPAM]})')
        print(f'OK count:       {predict_counts[tag.OK]} (truth: {truth_counts[tag.OK]})')
        print(f'FalsePos count: {confmat["fp"]} (Classified wrongly as SPAM)')
        print(f'TrueNeg count:  {confmat["fn"]} (Classified wrongly as OK)')
        print(f'Total count:    {sum(v for v in predict_counts.values())} (truth: {sum(v for v in truth_counts.values())})')
        print(f'Filter quality: {round(quality*100, 2)}% ({quality})')
        print('-'*30 + '\n')
    total_quality = sum(quality_outputs) / len(quality_outputs)
    print(f"Total quality:  {round(total_quality*100, 2)}% ({total_quality})")

def getInheritanceHierarchy(obj) -> str:
    def classHierarchy(cls):
        # If this class has no base classes, return its name
        if cls.__bases__ == (object,):
            return cls.__name__
        # Otherwise, return the name of this class and recurse on the first base class
        # Note: This assumes single inheritance
        return cls.__name__ + '(' + classHierarchy(cls.__bases__[0]) + ')'

    # Start the recursion with the class of the object
    return classHierarchy(obj.__class__)

if __name__ == "__main__":
    # Command line arguments parsing
    for arg in sys.argv[1:]:
        if arg in command_line_args.keys():
            command_line_args[arg] = not command_line_args[arg]
        else:
            raise ValueError(f'Command line argument "{arg}" not recognized!')
    main()
    # deletion of output based on command line args
    if command_line_args['del_output']:
        for path in CORPUS_LIST:
            filepath = os.path.join(path, PREDICTION_FNAME)
            if os.path.exists(filepath):
                os.remove(filepath)