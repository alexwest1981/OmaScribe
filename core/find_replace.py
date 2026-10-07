"""Literal and regular-expression search and replace for QTextDocument."""

from dataclasses import dataclass
import os
import re

from PyQt6.QtGui import QTextCursor, QTextDocument


@dataclass
class Match:
    start: int
    length: int
    text: str
    groups: list[str]
    block: int


def _compile(pattern: str, regex: bool, case_sensitive: bool, whole_word: bool):
    if not pattern:
        return None
    # stdlib re gives direct access to capture groups and Match.expand() for
    # backreferences, so replacement syntax needs only a small normalization.
    source = pattern if regex else re.escape(pattern)
    if whole_word:
        source = r"(?<!\w)(?:" + source + r")(?!\w)"
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        return re.compile(source, flags)
    except re.error as exc:
        raise ValueError(f"Invalid regular expression: {exc}") from exc


def _qt_offset(text: str, index: int) -> int:
    """Convert a Python character index to QTextCursor's UTF-16 offset."""
    return len(text[:index].encode("utf-16-le")) // 2


def find_all(document: QTextDocument, pattern: str, regex: bool = False,
             case_sensitive: bool = True, whole_word: bool = False,
             limit: int = 1000) -> list[Match]:
    compiled = _compile(pattern, regex, case_sensitive, whole_word)
    if compiled is None or limit <= 0:
        return []
    found = []
    block = document.begin()
    while block.isValid() and len(found) < limit:
        # Search each QTextBlock independently. Patterns cannot cross paragraph
        # boundaries; this mirrors Word's paragraph-scoped ^ and $ behavior.
        text = block.text()
        for result in compiled.finditer(text):
            found.append(Match(
                block.position() + _qt_offset(text, result.start()),
                _qt_offset(result.group(0), len(result.group(0))),
                result.group(0), list(result.groups()), block.blockNumber(),
            ))
            if len(found) >= limit:
                break
        block = block.next()
    return found


def _expanded_replacement(pattern: str, replacement: str, regex: bool, text: str) -> str:
    if not regex:
        return replacement
    # Accept both Python's \1 and Qt/Java-style $1 references.
    normalized = re.sub(r"\$(\d+)", r"\\g<\1>", replacement)
    try:
        return re.compile(pattern).match(text).expand(normalized)
    except (re.error, IndexError) as exc:
        raise ValueError(f"Invalid replacement backreference: {exc}") from exc


def _expand_groups(replacement: str, groups: list[str]) -> str:
    """Expand numbered references for a previously captured Match."""
    normalized = re.sub(r"\$(\d+)", r"\\g<\1>", replacement)
    token = re.compile(r"\\g<(\d+)>|\\([1-9][0-9]*)")

    def substitute(found):
        number = int(found.group(1) or found.group(2))
        if number > len(groups):
            raise ValueError(f"Invalid replacement backreference: no group {number}")
        return groups[number - 1] or ""

    return token.sub(substitute, normalized)


def replace_one(document: QTextDocument, match: Match, replacement: str,
                regex: bool = False) -> None:
    cursor = QTextCursor(document)
    cursor.setPosition(match.start)
    cursor.setPosition(match.start + match.length, QTextCursor.MoveMode.KeepAnchor)
    value = _expand_groups(replacement, match.groups) if regex else replacement
    cursor.insertText(value)


def replace_all(document: QTextDocument, pattern: str, replacement: str, **flags) -> int:
    matches = find_all(document, pattern, **flags)
    if not matches:
        return 0
    regex = flags.get("regex", False)
    # Replace from the highest offset down so earlier absolute offsets remain valid.
    cursor = QTextCursor(document)
    cursor.beginEditBlock()
    try:
        for match in reversed(matches):
            cursor.setPosition(match.start)
            cursor.setPosition(match.start + match.length, QTextCursor.MoveMode.KeepAnchor)
            value = _expanded_replacement(pattern, replacement, regex, match.text)
            cursor.insertText(value)
    finally:
        cursor.endEditBlock()
    return len(matches)


def _self_test():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    document = QTextDocument()
    document.setUndoRedoEnabled(True)
    document.setPlainText("Cat cat scatter\na1 b2")
    checks = 0

    result = find_all(document, "cat")
    assert len(result) == 2 and [item.text for item in result] == ["cat", "cat"]; checks += 1
    assert len(find_all(document, "cat", case_sensitive=False)) == 3; checks += 1
    assert len(find_all(document, "cat", case_sensitive=False, whole_word=True)) == 2; checks += 1
    assert len(find_all(document, "cat", case_sensitive=False, whole_word=True)[0].text) == 3; checks += 1
    grouped = find_all(document, r"([a-z])(\d)", regex=True)
    assert grouped[0].groups == ["a", "1"] and grouped[1].groups == ["b", "2"]; checks += 1

    document.setPlainText("a1 b2")
    count = replace_all(document, r"([a-z])(\d)", r"$2$1", regex=True)
    assert count == 2 and document.toPlainText() == "1a 2b"; checks += 1
    document.setPlainText("a a")
    assert replace_all(document, "a", "aa") == 2 and document.toPlainText() == "aa aa"; checks += 1
    document.setPlainText("a a")
    assert replace_all(document, "a", "b") == 2 and document.toPlainText() == "b b"; checks += 1
    cursor = QTextCursor(document)
    assert document.isUndoAvailable() and document.undo() is None and document.toPlainText() == "a a"; checks += 1
    try:
        find_all(document, "(", regex=True)
    except ValueError:
        checks += 1
    else:
        raise AssertionError("Invalid pattern did not raise ValueError")
    print(f"find_replace: {checks} kontroller gröna")
    return app


if __name__ == "__main__":
    _app = _self_test()
