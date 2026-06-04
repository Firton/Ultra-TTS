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

    def test_japanese_punctuation_and_closing_marks_are_preserved(self):
        text = "これはテストです。「句読点も確認します。」次の文です！最後です？"
        segments = text_pipeline.segment_text(text, 120)
        joined = " ".join(segment["text"] for segment in segments)

        self.assertIn("これはテストです。", joined)
        self.assertIn("「句読点も確認します。」", joined)
        self.assertIn("次の文です！", joined)
        self.assertIn("最後です？", joined)
        self.assertTrue(all(segment["text"].strip() for segment in segments))

    def test_mixed_japanese_english_text_is_preserved(self):
        text = "今日はUltra-TTSでlocal TTS workflowを確認します。Version one works."
        segments = text_pipeline.segment_text(text, 120)
        joined = " ".join(segment["text"] for segment in segments)

        self.assertIn("Ultra-TTS", joined)
        self.assertIn("local TTS workflow", joined)
        self.assertIn("Version one works.", joined)
        self.assertTrue(all(segment["text"].strip() for segment in segments))

    def test_mixed_japanese_english_product_terms_are_preserved(self):
        text = "Ultra-TTSはlocal TTS workflowを扱います。OpenAI APIだけに依存しない設計です。"
        segments = text_pipeline.segment_text(text, 120)
        joined = " ".join(segment["text"] for segment in segments)

        self.assertIn("Ultra-TTS", joined)
        self.assertIn("local TTS workflow", joined)
        self.assertIn("OpenAI API", joined)
        self.assertIn("依存しない設計", joined)

    def test_japanese_numbers_units_dates_amounts_and_versions_are_preserved(self):
        text = "2026年6月3日に3.5kgの荷物を1,200円で発送しました。v1.2.3の設定も確認します。温度は23.5℃です。"
        segments = text_pipeline.segment_text(text, 120)
        joined = " ".join(segment["text"] for segment in segments)

        for needle in ["2026年6月3日", "3.5kg", "1,200円", "v1.2.3", "23.5℃"]:
            self.assertIn(needle, joined)
        self.assertTrue(all(segment["text"].strip() for segment in segments))

    def test_long_form_segments_respect_max_length(self):
        text = (
            "第一段落です。これは長文分割の確認です。"
            " ".join(["日本語とEnglishを混ぜた文章です"] * 35)
        )
        segments = text_pipeline.segment_text(text, 100)

        self.assertGreater(len(segments), 1)
        self.assertTrue(all(segment["chars"] <= 100 for segment in segments))

    def test_long_form_japanese_sentence_segments_have_stable_metadata(self):
        text = "。".join([f"これは第{i}文です" for i in range(1, 40)]) + "。"
        segments = text_pipeline.segment_text(text, 100)

        self.assertGreater(len(segments), 1)
        self.assertTrue(all(segment["chars"] <= 100 for segment in segments))
        self.assertEqual([s["index"] for s in segments], list(range(1, len(segments) + 1)))
        self.assertTrue(all(s["id"] == f"seg-{s['index']:04d}" for s in segments))

    def test_punctuation_heavy_input_does_not_create_empty_segments(self):
        segments = text_pipeline.segment_text("。。。！？   \n\nこれは本文です。。。", 120)

        self.assertTrue(all(segment["text"].strip() for segment in segments))

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

    def test_clean_slug_removes_path_unsafe_characters(self):
        self.assertEqual(text_pipeline.clean_slug("../Private Voice: Test.wav"), "Private-Voice-Test.wav")
        self.assertEqual(text_pipeline.clean_slug("   "), "untitled")


if __name__ == "__main__":
    unittest.main()
