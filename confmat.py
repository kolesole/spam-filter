class BinaryConfusionMatrix:
    def __init__(self, pos_tag, neg_tag) -> None:
        self.pos_tag = pos_tag
        self.neg_tag = neg_tag
        self.tp = 0
        self.tn = 0
        self.fp = 0
        self.fn = 0
    
    def as_dict(self) -> dict:
        return {"tp": self.tp,
                "tn": self.tn,
                "fp": self.fp,
                "fn": self.fn}

    def update(self, truth, pred) -> None:
        match truth, pred:
            case self.pos_tag, self.pos_tag:
                self.tp += 1
            case self.pos_tag, self.neg_tag:
                self.fn += 1
            case self.neg_tag, self.pos_tag:
                self.fp += 1
            case self.neg_tag, self.neg_tag:
                self.tn += 1
            case _:
                raise ValueError((truth, pred))

    def compute_from_dicts(self, truth_dict:dict, pred_dict:dict) -> None:
        for key in truth_dict.keys():
            self.update(truth_dict[key], pred_dict[key])
