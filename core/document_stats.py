import re
from PyQt6.QtGui import QTextDocument

class DocumentStats:
    @staticmethod
    def analyze(text_document: QTextDocument):
        plain_text = text_document.toPlainText()
        
        words = re.findall(r'\b\w+\b', plain_text)
        word_count = len(words)
        char_count = len(plain_text)
        char_no_spaces = len(re.sub(r'\s+', '', plain_text))
        
        paragraphs = [p for p in plain_text.split('\n') if p.strip()]
        para_count = len(paragraphs)

        # Average reading speed ~ 200 words per minute
        reading_time_min = max(1, round(word_count / 200.0)) if word_count > 0 else 0

        # Extract headings outline
        outline = []
        block = text_document.begin()
        block_idx = 0
        while block.isValid():
            fmt = block.blockFormat()
            level = fmt.headingLevel()
            text = block.text().strip()
            if level in {1, 2, 3} and text:
                outline.append({
                    "level": level,
                    "text": text,
                    "block_index": block_idx,
                    "position": block.position()
                })
            block = block.next()
            block_idx += 1

        # Calculate Readability (LIX score suitable for English & Swedish)
        # LIX = (words / sentences) + (long_words * 100 / words)
        sentences = re.split(r'[.!?]+', plain_text)
        sentences = [s for s in sentences if s.strip()]
        sentence_count = max(1, len(sentences))
        
        long_words = [w for w in words if len(w) > 6]
        long_word_pct = (len(long_words) * 100.0 / max(1, word_count))
        words_per_sentence = word_count / sentence_count
        lix = round(words_per_sentence + long_word_pct) if word_count > 10 else 30

        readability_key = "lix_very_easy"
        readability_label = "Very Easy"
        if lix > 55:
            readability_key = "lix_very_difficult"
            readability_label = "Very Difficult / Academic"
        elif lix > 45:
            readability_key = "lix_difficult"
            readability_label = "Difficult / Advanced"
        elif lix > 35:
            readability_key = "lix_medium"
            readability_label = "Standard / Medium"
        elif lix > 25:
            readability_key = "lix_easy"
            readability_label = "Easy"

        return {
            "word_count": word_count,
            "char_count": char_count,
            "char_no_spaces": char_no_spaces,
            "para_count": para_count,
            "sentence_count": sentence_count,
            "reading_time_min": reading_time_min,
            "lix_score": lix,
            "readability_label": readability_label,
            "readability_key": readability_key,
            "outline": outline
        }


def sentence_ranges(text: str, max_words: int = 20):
    """Räckvidder (start, längd) för meningar som är tyngre än max_words ord.

    LIX drivs av orden per mening, och de långa meningarna är de som går att
    göra något åt. Lägena räknas i den text som skickades in, så anroparen kan
    markera dem utan att röra texten.
    """
    ranges = []
    for hit in re.finditer(r"[^.!?]+", text or ""):
        bit = hit.group(0)
        if len(re.findall(r"\b\w+\b", bit)) > max_words:
            ranges.append((hit.start(), len(bit)))
    return ranges


def _self_test() -> int:
    checks = 0
    kort = "En kort mening. Den här meningen har alldeles för många ord i sig och " \
           "borde därför plockas ut av analysen när gränsen är låg. Kort igen."
    träffar = sentence_ranges(kort, max_words=12)
    assert len(träffar) == 1, träffar; checks += 1
    start, längd = träffar[0]
    assert kort[start:start + längd].strip().startswith("Den här meningen"); checks += 1
    assert sentence_ranges(kort, max_words=100) == []; checks += 1
    assert sentence_ranges("") == [] and sentence_ranges(None) == []; checks += 1
    # flera tunga meningar i samma text ger flera räckvidder, i läsordning
    lång = "Kort. " + "Den ena mycket långa meningen med många ord i sig står här. " \
                        "Och den andra lika långa meningen med många ord står också här."
    träffar = sentence_ranges(lång, max_words=8)
    assert len(träffar) == 2 and träffar[0][0] < träffar[1][0]; checks += 1
    print(f"document_stats: {checks} kontroller gröna")
    return checks


if __name__ == "__main__":
    _self_test()
