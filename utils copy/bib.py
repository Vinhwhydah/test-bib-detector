import re
from detect.model import BibMatch

def check_bib_number(bib_number):
    full_pattern = r'^[a-zA-Z]?\d{3,6}$'
    partial_pattern = r"^\d{3,6}$"
    full_match = re.match(full_pattern, bib_number)
    partial_match = re.match(partial_pattern, bib_number)

    if full_match:
        return BibMatch.FULL
    elif partial_match:
        return BibMatch.PARTIAL
    else:
        return BibMatch.NOT_MATCH