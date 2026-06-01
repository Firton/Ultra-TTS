import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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

    def test_japanese_punctuation_does_not_create_empty_segments(self):
        segments = text_pipeline.segment_text(
            "第一段落です。。「引用文です。」\n\n第二段落です？！終わりです。",
            120,
        )

        self.assertGreaterEqual(len(segments), 2)
        self.assertTrue(all(segment["text"].strip() for segment in segments))
        self.assertTrue(all(segment["chars"] == len(segment["text"]) for segment in segments))

    def test_segment_ids_and_indexes_are_stable(self):
        segments = text_pipeline.segment_text("One sentence. Two sentence. Three sentence.", 80)

        self.assertEqual([segment["id"] for segment in segments], ["seg-0001"])
        self.assertEqual([segment["index"] for segment in segments], [1])
        self.assertEqual(segments[0]["paragraphIndex"], 1)

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            text_pipeline.segment_text("  \n\n  ", 120)

    def test_rejects_too_small_segment_limit(self):
        with self.assertRaises(ValueError):
            text_pipeline.segment_text("Short text.", 79)

    def test_relative_url_path_uses_forward_slashes(self):
        root = ROOT / "outputs"
        path = root / "web" / "sample.manifest.json"

        self.assertEqual(
            text_pipeline.relative_url_path(path, root),
            "web/sample.manifest.json",
        )


if __name__ == "__main__":
    unittest.main()
