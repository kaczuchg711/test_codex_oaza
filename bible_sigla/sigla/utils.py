from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

import pythonbible as pb
import pytesseract
from PIL import Image, ImageOps
from pytesseract import TesseractNotFoundError


class SiglaExtractionError(RuntimeError):
    """Raised when the OCR pipeline cannot be executed."""


@dataclass(slots=True)
class ReferenceResult:
    """A resolved Bible reference with rendered scripture text."""

    label: str
    text: str


DEFAULT_VERSION: pb.Version = pb.Version.KING_JAMES


def _normalize_key(raw: str) -> str:
    """Return an uppercase key without diacritics, dots or spaces."""

    normalized = unicodedata.normalize("NFKD", raw).replace("Ł", "L").replace("ł", "l")
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[\s\.]", "", without_marks)
    return cleaned.upper()


_RAW_BOOK_ALIASES: dict[pb.Book, tuple[str, ...]] = {
    pb.Book.GENESIS: ("RDZ", "RODZ", "GEN"),
    pb.Book.EXODUS: ("WJ", "WYJ", "EX", "EXODUS"),
    pb.Book.LEVITICUS: ("KPL", "LEV"),
    pb.Book.NUMBERS: ("LB", "LICZB", "NUM"),
    pb.Book.DEUTERONOMY: ("PWT", "DEUT"),
    pb.Book.JOSHUA: ("JOZ", "JOS"),
    pb.Book.JUDGES: ("SDZ", "SEDZ", "JDG"),
    pb.Book.RUTH: ("RT", "RUT"),
    pb.Book.SAMUEL_1: ("1SM", "1SAM", "ISM"),
    pb.Book.SAMUEL_2: ("2SM", "2SAM", "IISM"),
    pb.Book.KINGS_1: ("1KRL", "1KRO", "1KGS"),
    pb.Book.KINGS_2: ("2KRL", "2KRO", "2KGS"),
    pb.Book.CHRONICLES_1: ("1KRN", "1KRON"),
    pb.Book.CHRONICLES_2: ("2KRN", "2KRON"),
    pb.Book.EZRA: ("EZD", "EZRA"),
    pb.Book.NEHEMIAH: ("NE", "NEH"),
    pb.Book.ESTHER: ("EST",),
    pb.Book.JOB: ("HI", "JOB"),
    pb.Book.PSALMS: ("PS", "PSLM"),
    pb.Book.PROVERBS: ("PRZ", "PRZYP", "PR"),
    pb.Book.ECCLESIASTES: ("KOH", "KOHELET"),
    pb.Book.SONG_OF_SONGS: ("PNP", "PIESN", "PNS"),
    pb.Book.ISAIAH: ("IZ", "ISA"),
    pb.Book.JEREMIAH: ("JR", "JER"),
    pb.Book.LAMENTATIONS: ("LM", "LAM"),
    pb.Book.EZEKIEL: ("EZ", "EZE"),
    pb.Book.DANIEL: ("DN", "DAN"),
    pb.Book.HOSEA: ("OZ", "HOS"),
    pb.Book.JOEL: ("JL", "JOEL"),
    pb.Book.AMOS: ("AM",),
    pb.Book.OBADIAH: ("ABD", "OB"),
    pb.Book.JONAH: ("JON",),
    pb.Book.MICAH: ("MI", "MIC"),
    pb.Book.NAHUM: ("NA",),
    pb.Book.HABAKKUK: ("HA", "HAB"),
    pb.Book.ZEPHANIAH: ("SO", "SOP"),
    pb.Book.HAGGAI: ("AG", "HAG"),
    pb.Book.ZECHARIAH: ("ZA", "ZACH"),
    pb.Book.MALACHI: ("ML", "MAL"),
    pb.Book.MATTHEW: ("MT", "MAT"),
    pb.Book.MARK: ("MK", "MRK"),
    pb.Book.LUKE: ("LK", "LUK"),
    pb.Book.JOHN: ("J", "JAN", "JN"),
    pb.Book.ACTS: ("DZ", "DAP", "DZAP"),
    pb.Book.ROMANS: ("RZ", "ROM"),
    pb.Book.CORINTHIANS_1: ("1KOR", "IKOR"),
    pb.Book.CORINTHIANS_2: ("2KOR", "IIKOR"),
    pb.Book.GALATIANS: ("GA", "GAL"),
    pb.Book.EPHESIANS: ("EF", "EPH"),
    pb.Book.PHILIPPIANS: ("FLP", "PHP"),
    pb.Book.COLOSSIANS: ("KOL", "COL"),
    pb.Book.THESSALONIANS_1: ("1TES", "1TESAL"),
    pb.Book.THESSALONIANS_2: ("2TES", "2TESAL"),
    pb.Book.TIMOTHY_1: ("1TM", "1TIM"),
    pb.Book.TIMOTHY_2: ("2TM", "2TIM"),
    pb.Book.TITUS: ("TT", "TIT"),
    pb.Book.PHILEMON: ("FLM", "PHM"),
    pb.Book.HEBREWS: ("HBR", "HEB"),
    pb.Book.JAMES: ("JK", "JAK"),
    pb.Book.PETER_1: ("1P", "1PI", "1PTR"),
    pb.Book.PETER_2: ("2P", "2PI", "2PTR"),
    pb.Book.JOHN_1: ("1J", "1JAN", "1JN"),
    pb.Book.JOHN_2: ("2J", "2JAN", "2JN"),
    pb.Book.JOHN_3: ("3J", "3JAN", "3JN"),
    pb.Book.JUDE: ("JUD",),
    pb.Book.REVELATION: ("AP", "APK", "OBJ", "OBJAW"),
    pb.Book.TOBIT: ("TB", "TOB"),
    pb.Book.WISDOM_OF_SOLOMON: ("MDR", "WIS"),
    pb.Book.ECCLESIASTICUS: ("SYR", "SIR"),
    pb.Book.MACCABEES_1: ("1MCH", "1MAC"),
    pb.Book.MACCABEES_2: ("2MCH", "2MAC"),
}

_BOOK_ALIASES: dict[str, pb.Book] = {}
for book, keys in _RAW_BOOK_ALIASES.items():
    for key in keys:
        _BOOK_ALIASES[key] = book
_REFERENCE_PATTERN = re.compile(
    r"(?P<book>(?:[1-3]\s*)?[A-Za-zĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\.]+)\s+" r"(?P<chapter>\d{1,3})(?:[,:](?P<verses>[\d\-–—,.\s]+))?"
)


def extract_text(image_file) -> str:
    """Run OCR on the uploaded image and return the raw text."""

    image_file.seek(0)
    with Image.open(image_file) as image:
        grayscale = ImageOps.grayscale(image)
        enhanced = ImageOps.autocontrast(grayscale)
        try:
            text = pytesseract.image_to_string(enhanced, lang="pol+eng")
        except TesseractNotFoundError as exc:
            raise SiglaExtractionError(
                "Nie odnaleziono silnika Tesseract. Zainstaluj go lokalnie i ustaw w PATH."
            ) from exc
    image_file.seek(0)
    return text


def _book_from_match(raw_book: str) -> pb.Book | None:
    return _BOOK_ALIASES.get(_normalize_key(raw_book))


def _build_reference(book: pb.Book, chapter: int, verses: str | None) -> Iterable[pb.NormalizedReference]:
    base_title = pb.get_book_titles(book, DEFAULT_VERSION).short_title

    sanitized_verses = ""
    if verses:
        primary = verses.split(';', 1)[0]
        sanitized_verses = (
            primary.replace(" ", "")
            .replace("–", "-")
            .replace("—", "-")
            .replace("..", ",")
            .replace(".", ",")
        )
        sanitized_verses = sanitized_verses.lstrip(":")
        sanitized_verses = sanitized_verses.strip(',')

    reference_string = f"{base_title} {chapter}"
    if sanitized_verses:
        if not sanitized_verses.startswith(":") and not sanitized_verses.startswith(","):
            reference_string += ":"
        reference_string += sanitized_verses

    try:
        references = pb.get_references(reference_string)
    except pb.InvalidBibleParserError:
        return []

    return references


def find_references(text: str) -> list[pb.NormalizedReference]:
    """Parse OCR text and return normalized Bible references."""

    normalized_text = text.replace("\n", " ")
    references: list[pb.NormalizedReference] = []
    seen: set[tuple] = set()

    for match in _REFERENCE_PATTERN.finditer(normalized_text):
        book = _book_from_match(match.group("book"))
        if not book:
            continue

        chapter = int(match.group("chapter"))
        verses = match.group("verses")

        for reference in _build_reference(book, chapter, verses):
            key = (
                reference.book,
                reference.start_chapter,
                reference.start_verse,
                reference.end_chapter,
                reference.end_verse,
            )
            if key in seen:
                continue
            seen.add(key)
            references.append(reference)

    return references


def resolve_references(references: Iterable[pb.NormalizedReference]) -> list[ReferenceResult]:
    """Fetch formatted scripture passages for the provided references."""

    results: list[ReferenceResult] = []

    for reference in references:
        verse_ids = pb.convert_references_to_verse_ids([reference])
        if not verse_ids:
            continue
        passage = pb.format_scripture_text(
            verse_ids,
            format_type="plain_text",
            include_verse_numbers=True,
            version=DEFAULT_VERSION,
        ).strip()
        label = pb.format_single_reference(reference, version=DEFAULT_VERSION)
        results.append(ReferenceResult(label=label, text=passage))

    return results
