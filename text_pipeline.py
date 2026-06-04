import re
import time
from pathlib import Path


SENTENCE_ENDINGS = set("。．.!！?？")
CLOSING_MARKS = set("」』”’\")】〕］）》〉")
SOFT_BREAKS = ["、", "，", ",", "；", ";", "：", ":", " "]
HARD_WRAP_MARGIN = 24


def timestamp():
    return time.strftime("%Y%m%d-%H%M%S")


def normalize_text(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def clean_slug(value, default="untitled"):
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip()).strip("-._")
    return slug[:80] or default


def split_paragraphs(text):
    normalized = normalize_text(text)
    if not normalized:
        return []

    paragraphs = []
    buffer = []
    for line in normalized.split("\n"):
        stripped = line.strip()
        if not stripped:
            if buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = []
            continue
        buffer.append(stripped)

    if buffer:
        paragraphs.append(" ".join(buffer).strip())

    return paragraphs


def is_sentence_ending(paragraph, index):
    char = paragraph[index]
    if char not in SENTENCE_ENDINGS:
        return False

    if char == ".":
        previous_char = paragraph[index - 1] if index > 0 else ""
        next_char = paragraph[index + 1] if index + 1 < len(paragraph) else ""

        if previous_char.isdigit() and next_char.isdigit():
            return False
        if previous_char.isalnum() and next_char.isalnum():
            return False

    return True


def split_sentences(paragraph):
    paragraph = re.sub(r"\s+", " ", (paragraph or "").strip())
    if not paragraph:
        return []

    sentences = []
    start = 0
    index = 0
    while index < len(paragraph):
        if is_sentence_ending(paragraph, index):
            end = index + 1
            while end < len(paragraph) and paragraph[end] in CLOSING_MARKS:
                end += 1
            sentence = paragraph[start:end].strip()
            if sentence:
                sentences.append(sentence)
            while end < len(paragraph) and paragraph[end].isspace():
                end += 1
            start = end
            index = end
            continue
        index += 1

    tail = paragraph[start:].strip()
    if tail:
        sentences.append(tail)

    return sentences


def split_oversized_text(text, max_chars):
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    for separator in SOFT_BREAKS:
        parts = split_by_separator(text, separator, max_chars)
        if len(parts) > 1 and all(len(part) <= max_chars for part in parts):
            return parts

    return hard_wrap(text, max_chars)


def split_by_separator(text, separator, max_chars):
    raw_parts = text.split(separator)
    if len(raw_parts) <= 1:
        return [text]

    chunks = []
    current = ""
    for raw_part in raw_parts:
        part = raw_part.strip()
        if not part:
            continue
        candidate = join_with_separator(current, part, separator)
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = part
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks or [text]


def join_with_separator(left, right, separator):
    if not left:
        return right
    if separator == " ":
        return f"{left} {right}"
    return f"{left}{separator}{right}"


def hard_wrap(text, max_chars):
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            window_start = max(start, end - HARD_WRAP_MARGIN)
            whitespace = text.rfind(" ", window_start, end)
            if whitespace > start:
                end = whitespace
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
        while start < len(text) and text[start].isspace():
            start += 1
    return chunks


def pack_sentences(sentences, max_chars):
    chunks = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        pieces = split_oversized_text(sentence, max_chars)
        for piece in pieces:
            candidate = f"{current} {piece}".strip() if current else piece
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = piece
            else:
                current = candidate

    if current:
        chunks.append(current)
    return chunks


def segment_text(text, max_chars):
    if max_chars < 80:
        raise ValueError("max_chars must be at least 80.")

    paragraphs = split_paragraphs(text)
    segments = []

    for paragraph_index, paragraph in enumerate(paragraphs, start=1):
        sentences = split_sentences(paragraph)
        chunks = pack_sentences(sentences, max_chars)
        for chunk in chunks:
            segments.append(
                {
                    "id": f"seg-{len(segments) + 1:04d}",
                    "index": len(segments) + 1,
                    "paragraphIndex": paragraph_index,
                    "text": chunk,
                    "chars": len(chunk),
                }
            )

    if not segments:
        raise ValueError("Text is empty.")
    return segments


def relative_url_path(path, root):
    relative = Path(path).resolve().relative_to(Path(root).resolve())
    return "/".join(relative.parts)
