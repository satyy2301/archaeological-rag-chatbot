"""Regression tests for PDF text extraction and chunking."""

import time
import unittest

from pdf_processor import PDFProcessor


class PDFProcessorChunkTests(unittest.TestCase):
    def test_chunk_long_line_no_periods(self):
        text = "T1 L5 C12 pottery " * 1200  # ~22k chars, no sentence delimiters
        started = time.perf_counter()
        chunks = PDFProcessor.split_text_chunks(text, chunk_size=1000, chunk_overlap=200)
        elapsed = time.perf_counter() - started

        self.assertGreater(len(chunks), 0)
        self.assertLess(elapsed, 1.0)
        self.assertLessEqual(len(chunks), 40)

    def test_chunk_table_mash(self):
        text = " ".join(
            f"T{t} L{l} C{c} pottery" for t in range(1, 6) for l in range(1, 6) for c in range(1, 4)
        )
        chunks = PDFProcessor.split_text_chunks(text, chunk_size=500, chunk_overlap=50)
        self.assertGreater(len(chunks), 0)
        joined = " ".join(chunks)
        self.assertIn("T1", joined)
        self.assertIn("pottery", joined)

    def test_normalize_collapses_whitespace(self):
        raw = "Trench\x001\n\n\n\nLocus   5   Context 12"
        normalized = PDFProcessor._normalize_extracted_text(raw)
        self.assertNotIn("\x00", normalized)
        self.assertNotIn("\n\n\n", normalized)
        self.assertIn("Locus  5", normalized)

    def test_format_table(self):
        table = [
            ["Trench", "Locus", "Find"],
            ["T1", "L5", "pottery sherd"],
            [None, "L6", "bone"],
        ]
        formatted = PDFProcessor._format_table(table)
        self.assertIn("Trench | Locus | Find", formatted)
        self.assertIn("T1 | L5 | pottery sherd", formatted)
        self.assertIn("L6 | bone", formatted)

    def test_split_empty_text(self):
        self.assertEqual(PDFProcessor.split_text_chunks(""), [])


if __name__ == "__main__":
    unittest.main()
