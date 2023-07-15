from enum import Enum


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


class BibMatch(Enum):
    FULL = 1
    PARTIAL = 2
    NOT_MATCH = 0
