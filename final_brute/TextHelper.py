import re

# words that commonly appear in spam emails. Serves as potential indicator of spam.
spam_keywords = [
    "porn", "erotic", "sex", "penis", "viagra", "free", "winner", 
    "congratulations", "urgent", "important", "guaranteed", 
    "winner", "rich", "millionaire", "billionaire", "lottery", 
    "sweepstakes", "prize", "claim", "offer", "limited time", 
    "pharmacy", "medication", "loan", "debt", "weight loss", 
    "replica", "hot", "adult", "xxx",
    "girls", "teens", "sensual", "sexy"
]


regex_to_alnum = re.compile('[^a-zA-Z0-9]')
# returns given string where all alphanum characters have been removed. uses regex for efficiency.
def to_alnum(input_string) -> str:
    return regex_to_alnum.sub('', input_string)

# iterates over words in given string. parses username if email or and domain if url is detected
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

# returns first full email address like sibstring from given string
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
