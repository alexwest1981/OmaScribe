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

        readability_label = "Very Easy"
        if lix > 55:
            readability_label = "Very Difficult / Academic"
        elif lix > 45:
            readability_label = "Difficult / Advanced"
        elif lix > 35:
            readability_label = "Standard / Medium"
        elif lix > 25:
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
            "outline": outline
        }
