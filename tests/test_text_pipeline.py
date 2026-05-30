import unittest

import text_pipeline


class TextPipelineTests(unittest.TestCase):
    def test_splits_paragraphs_and_packs_short_sentences(self):
        segments = text_pipeline.segment_text(
            "これは一文目です。これは二文目です。\n\nThis is another paragraph. It is short.",
            120,
        )

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["paragraphIndex"], 1)
        self.assertEqual(segments[1]["paragraphIndex"], 2)

    def test_wraps_oversized_sentence(self):
        text = " ".join(["abcdef"] * 40)
        segments = text_pipeline.segment_text(text, 80)

        self.assertGreater(len(segments), 1)
        self.assertTrue(all(segment["chars"] <= 80 for segment in segments))

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            text_pipeline.segment_text("  \n\n  ", 120)


if __name__ == "__main__":
    unittest.main()
