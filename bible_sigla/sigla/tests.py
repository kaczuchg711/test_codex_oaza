from __future__ import annotations

from django.test import TestCase

import pythonbible as pb

from .utils import DEFAULT_VERSION, find_references, resolve_references


class ReferenceParsingTests(TestCase):
    def test_find_references_parses_polish_sigla(self) -> None:
        text = "Plan spotkania: Mt 5,1-3; Łk 2,8-14; 1 Kor 13,1-3."

        references = find_references(text)
        pairs = {(ref.book, ref.start_chapter, ref.start_verse, ref.end_verse) for ref in references}

        self.assertIn((pb.Book.MATTHEW, 5, 1, 3), pairs)
        self.assertIn((pb.Book.LUKE, 2, 8, 14), pairs)
        self.assertIn((pb.Book.CORINTHIANS_1, 13, 1, 3), pairs)

    def test_resolve_references_fetches_passages(self) -> None:
        reference = pb.get_references("Matthew 5:1-3")[0]

        results = resolve_references([reference])

        self.assertEqual(results[0].label, pb.format_single_reference(reference, version=DEFAULT_VERSION))
        self.assertTrue(results[0].text)
