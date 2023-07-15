import re
from detect import model
from utils.bib import check_bib_number
from utils.bounding import normalized_bounding_box_vertices


def handle_full_text_annotation(full_text_annotation, width, height):
    texts = []
    bibs = []

    # Collect specified feature bounds by enumerating all document features
    for page in full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                temps = []

                for word in paragraph.words:
                    symbols = []
                    for symbol in word.symbols:
                        symbols.append(symbol.text)

                    word_text = "".join(symbols)

                    match = check_bib_number(word_text)

                    texts.append({
                        'value': word_text,
                        'confidence': word.confidence,
                        'bound': normalized_bounding_box_vertices(word.bounding_box, width, height)
                    })

                    if match != model.BibMatch.NOT_MATCH and word.confidence >= 0.6:
                        # match_type = 'full' if match == model.BibMatch.FULL else 'partial'
                        bibs.append({
                            'value': word_text,
                            'confidence': word.confidence,
                            'bound': normalized_bounding_box_vertices(word.bounding_box, width, height)
                        })

    return bibs, texts





