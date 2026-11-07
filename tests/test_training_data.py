import tempfile
import unittest
from pathlib import Path

from transformers import AutoTokenizer

from hakkillo.data import encode_example, ensure_disjoint, read_examples
from hakkillo.settings import BASE_MODEL, BASE_REVISION, ROOT


class TrainingDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION)

    def test_all_examples_have_response_only_supervision(self):
        for path in (ROOT / "data/train.jsonl", ROOT / "data/eval.jsonl"):
            for row in read_examples(path):
                encoded = encode_example(self.tokenizer, row)
                target = encoded["labels"][0]
                self.assertTrue((target == -100).any())
                response = self.tokenizer.decode(target[target != -100], skip_special_tokens=True).strip()
                self.assertEqual(response, row["response"])

    def test_splits_are_separate(self):
        ensure_disjoint(read_examples(ROOT / "data/train.jsonl"), read_examples(ROOT / "data/eval.jsonl"))

    def test_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            ensure_disjoint([{"prompt": "Hello "}], [{"prompt": "hello"}])

    def test_truncation_cannot_silently_remove_the_answer(self):
        with self.assertRaises(ValueError):
            encode_example(self.tokenizer, {"prompt": "hello " * 100, "response": "Hello"}, max_length=16)

    def test_empty_and_duplicate_data_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_examples(path)
            path.write_text('{"prompt":"hello","response":"hi"}\n' * 2, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_examples(path)


if __name__ == "__main__":
    unittest.main()
