from urllib.parse import urlparse
import re

spam_keywords = [
    "porn", "erotic", "sex", "penis", "viagra", "free", "winner", 
    "congratulations", "urgent", "important", "guaranteed", 
    "winner", "rich", "millionaire", "billionaire", "lottery", 
    "sweepstakes", "prize", "claim", "offer", "limited time", 
    "pharmacy", "medication", "loan", "debt", "weight loss", 
    "replica", "hot", "adult", "xxx",
    "girls", "teens", "sensual", "sexy"
]

spam_keywords_ = [
    "viagra", "free", "winner", "urgent", "millionaire", 
    "lottery", "sweepstakes", "prize", "claim", "discount", 
    "pharmacy", "medication", "loan", "credit", "cheap",
    "replica", "adult", "xxx", "unsecured", "mortgage",
    "pre-approved", "bankruptcy", "risk-free", "hidden charges",
    "special promotion", "bonus", "fake", "fraud", "scam",
    "not spam", "confidential", "password", "verify your account",
    "account suspended", "security alert"
]

def compute_word_frequencies(filename):
    with open(filename, "r+", encoding='utf-8') as open_file:
        read_file = open_file.readlines()
        dic = {}

        for i in read_file:
            ls = i.split()
            for j in ls:
                dic[j] = 0
        for i in read_file:
            ls = i.split()
            for j in ls:
                dic[j] += 1
        return dic

regex_to_alnum = re.compile('[^a-zA-Z0-9]')
def to_alnum(input_string) -> str:
    return regex_to_alnum.sub('', input_string)

def is_string_url(input_string:str) -> str:
    try:
        result = urlparse(input_string)
        return result
    except Exception:
        return False

def word_iterator(input_string:str) -> str:
    for word in input_string.lower().split():
        # If word doesn't contain any letter, skip
        if not any(char.isalpha() for char in word):
            continue
        
        # if '@' in word, consider it as email address and parse.
        if '@' in word and '.' in word:
            addr = parse_full_email_addr_from_str(word)
            if addr:
                yield addr
        
        # if word is url address, parse domain name and return
        addr_indicators = ['http:', 'https:', 'www.', '.com']
        if '.' in word and any(ind in word for ind in addr_indicators):
            parts = word.split('.')
            if len(parts) <= 2:
                yield to_alnum(parts[0])
            elif len(parts) > 2:
                yield to_alnum(parts[1])
        
        yield to_alnum(word)

def parse_email_addr_username(FROM_str:str) -> str:
    for addr in FROM_str.lower().split():
        if addr.count("@") != 1:
            continue
        username = addr.split('@')[0]
        return to_alnum(username)
    return ""

def parse_email_addr_domain(FROM_str:str) -> str:
    for addr in FROM_str.split():
        if addr.count("@") != 1:
            continue
        domain = addr.split('@')[-1]
        while not domain[-1].isalnum():
            domain = domain[:-1]
        return domain
    return ""

def parse_full_email_addr_from_str(FROM_str:str) -> str:
    for addr in FROM_str.split():
        if addr.count("@") != 1:
            continue
        username, domain = addr.lower().split('@')
        while domain and not domain[-1].isalnum():
            domain = domain[:-1]
        while username and not username[0].isalnum():
            username = username[1:]
        
        if username and domain:
            return username + "@" + domain
    return ''
