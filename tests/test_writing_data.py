import hashlib
import json
import unittest

from transformers import AutoTokenizer
from hakkillo.data import encode_example, ensure_disjoint, read_examples
from hakkillo.settings import BASE_MODEL, BASE_REVISION, ROOT


class WritingDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = ROOT / "data/v0.2"
        cls.train = read_examples(cls.folder / "train.jsonl")
        cls.dev = read_examples(cls.folder / "writing_dev.jsonl")
        cls.holdout = read_examples(cls.folder / "writing_holdout.jsonl")
        cls.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION)

    def test_no_source_or_prompt_leakage_between_splits(self):
        groups = [self.train, self.dev, self.holdout]
        for a, b in ((0, 1), (0, 2), (1, 2)):
            ensure_disjoint(groups[a], groups[b])
            left = {" ".join(r["source"].casefold().split()) for r in groups[a] if "source" in r}
            right = {" ".join(r["source"].casefold().split()) for r in groups[b] if "source" in r}
            self.assertFalse(left & right)

    def test_targets_survive_tokenization_without_prompt_supervision(self):
        for row in self.train + self.dev + self.holdout:
            encoded = encode_example(self.tokenizer, row, max_length=256)
            labels = encoded["labels"][0]
            self.assertTrue((labels == -100).any())
            self.assertEqual(self.tokenizer.decode(labels[labels != -100], skip_special_tokens=True).strip(), row["response"])

    def test_manifest_matches_files_and_counts(self):
        manifest = json.loads((self.folder / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(self.train), manifest["training_examples"])
        self.assertEqual(len(self.dev), 50)
        self.assertEqual(len(self.holdout), 20)
        for name, digest in manifest["sha256"].items():
            self.assertEqual(hashlib.sha256((self.folder / name).read_bytes()).hexdigest(), digest)

    def test_reference_answers_preserve_required_literals(self):
        for row in self.dev + self.holdout:
            for required in row.get("preserve", []):
                self.assertIn(required, row["response"], row["id"])


if __name__ == "__main__":
    unittest.main()
