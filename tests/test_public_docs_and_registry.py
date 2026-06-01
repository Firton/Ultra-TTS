import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import local_paths
import model_registry


class PublicDocsAndRegistryTests(unittest.TestCase):
    def test_readme_links_public_evidence_docs(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for needle in [
            "THIRD_PARTY_MODELS.md",
            "docs/demo.md",
            "docs/maintainer-notes.md",
        ]:
            self.assertIn(needle, readme)

    def test_third_party_model_docs_warn_against_redistribution(self):
        text = (ROOT / "THIRD_PARTY_MODELS.md").read_text(encoding="utf-8").lower()

        for phrase in [
            "does not commit",
            "model weights",
            "generated audio",
            "do not redistribute model files unless upstream permits it",
            "check upstream",
        ]:
            self.assertIn(phrase, text)

    def test_demo_doc_does_not_commit_audio_samples(self):
        text = (ROOT / "docs" / "demo.md").read_text(encoding="utf-8").lower()

        self.assertIn("docs/images/ultra-tts-web-ui.png", text)
        self.assertIn("does not commit generated audio samples", text)
        self.assertIn("must not include", text)

    def test_model_registry_has_stable_lightweight_metadata(self):
        expected_detail_ids = {
            "piper",
            "orpheus",
            "kokoro",
            "chatterbox",
            "dia",
            "mlx-chatterbox",
            "mlx-qwen3-tts",
            "mlx-kokoro",
            "mlx-dia",
        }
        self.assertTrue(expected_detail_ids.issubset(model_registry.MODEL_DETAILS))

        for model_id, meta in model_registry.HF_MODELS.items():
            self.assertEqual(model_id.strip(), model_id)
            self.assertTrue(meta["name"])
            self.assertTrue(meta["backend"])
            self.assertIsInstance(meta["requiredFiles"], list)
            self.assertTrue(meta["requiredFiles"])
            self.assertTrue(Path(meta["path"]).is_relative_to(local_paths.MODELS_DIR))


if __name__ == "__main__":
    unittest.main()
