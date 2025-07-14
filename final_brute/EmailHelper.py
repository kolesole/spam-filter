from html.parser import HTMLParser
from FileHelper import TRUTH_FNAME
import email
import os, re
from Tags import tag

# helper class for parsing data form email files
class EmailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.plain_text = ""
    
    # handling data inn between html tags
    def handle_data(self, data: str) -> None:
        self.plain_text += '\n' + data

# returns true if string seems to contain html data
def is_string_html(string:str) -> bool:
    common_html_tags = [
    "<html", "<head", "<title",
    "<body", "<h1", "<h2", "<h3", "<h4", "<h5", "<h6",
    "<p", "<a", "<img",
    "<ul", "<ol", "<li",
    "<div", "<span",
    "<table", "<tr", "<td", "<th",
    "<br", "<hr",
    "<form", "<input", "<button",
    "<style", "<script"
    ]
    for tag in common_html_tags:
        if tag in string or tag.upper() in string:
            return True
    return False

# regex function for stripping HTML elements from string and only keeping raw text data
def strip_html(html):
    # Remove inline JavaScript/CSS:
    html = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html)
    # Remove html comments. This must be done before removing regular tags.
    html = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", html)
    # Remove HTML tags:
    html = re.sub(r"<.*?>", "", html)
    # Substitute multiple spaces with single space
    html = re.sub(r"\s+", " ", html)
    # Remove leading and trailing spaces
    html = html.strip()
    # Replace HTML entities with their corresponding characters
    html = re.sub('&lt;', '<', html)
    html = re.sub('&gt;', '>', html)
    html = re.sub('&amp;', '&', html)
    html = re.sub('&quot;', '"', html)
    html = re.sub('&#39;', "'", html)
    return html

# reads email from path and returns dict of of parsed data with both keys and values as strings
def read_email_from_file(email_path:str, truth_path = "") -> dict:
    # parsing header information
    text = ""
    with open(email_path, "r", encoding="utf-8") as f:
        text = f.read()
    head = email.message_from_string(text)
    output_dict = {key.lower(): value.lower() if type(value) == str else value for key, value in head.items()}
    
    # parsing body text
    body = head.get_payload()
    if type(body) in (list, tuple):
        body = body[0].as_string()
    
    # stripping html
    parser = EmailParser()
    parser.feed(body)
    stripped_body = strip_html(parser.plain_text)
    output_dict[tag.BODY] = stripped_body.lower().replace('\t', '').replace('\n', '')
    
    # Add aditional information to dictionary (email path, name, etc..)
    email_filename = email_path.split(os.sep)[-1]
    output_dict[tag.NAME] = email_filename
    output_dict[tag.PATH] = email_path

    # If truth file is available, add truth tag
    output_dict[tag.TRUTH] = get_email_truth(email_filename, truth_path) if truth_path else tag.NA

    return output_dict

# Iterates over email files from given corpus directory path. Yields dictionary for each email containing email data.
def email_iterator(corpus_dir:str, load_truth=True) -> dict:
    files = os.listdir(corpus_dir)
    truth_path = ""
    if TRUTH_FNAME in files and load_truth:
        truth_path = os.path.join(corpus_dir, TRUTH_FNAME)
    for fname in files:
        if not fname.startswith("!"):
            yield read_email_from_file(os.path.join(corpus_dir, fname), truth_path)

# returns email's truth tag (SPAM or OK) parsed from provided !truth.txt file path.
def get_email_truth(email_filename:str, truth_path:str) -> str:
    with open(truth_path, "r", encoding="utf-8") as f:
        for row in f.readlines():
            filename, truth = row.removesuffix("\n").split(" ")
            if filename == email_filename:
                return truth
    return tag.NA