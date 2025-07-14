# enum-like class of commonly used headers, strings, tags and similar strings
class tag:
    ### non email dict tags ###
    SPAM = 'SPAM'           # truth tag
    OK = 'OK'               # truth tag
    HEADER_NAMES = 'header_names'           # boolean, not a header. see context of usage.
    COMMON_SPAM_WORDS = 'common_spam_words' # boolean, not a header. see context of usage.
    NA = 'unavailable'      # represents missing or unavailable value
    ### email dict tags ###
    TRUTH = 'truth'         # always present
    NAME = 'name'           # always present
    PATH = 'path'           # always present
    BODY = 'body'           # always present
    FROM = 'from'           # seems to be always present based on available data
    SUBJECT = 'subject'     # seems to be always present based on available data
    CC = 'cc'
    TO = 'to'
    DELIVERED_TO = 'delivered-to'
    LIST_ID = 'list-id'
    LIST_HELP = 'list-help'
    SENDER = 'sender'
    RECEIVED = 'received'
    RETURN_PATH = 'return-path'
    MESSAGE_ID = 'message-id'
    CONTENT_TYPE = 'content-type'
    CONTENT_TRANSFER_ENCODING = 'content-transfer-encoding'
    ORGANISATION = 'organisation'

HEADERS_CONTAINING_EMAIL_ADDRESSES = (tag.FROM, tag.TO, tag.CC, tag.DELIVERED_TO, tag.LIST_HELP, tag.SENDER, tag.RETURN_PATH)

