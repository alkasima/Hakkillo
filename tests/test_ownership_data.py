import copy
import hashlib
import json
import unittest

from transformers import AutoTokenizer

from hakkillo.data import encode_example
from hakkillo.settings import BASE_MODEL, BASE_REVISION
from scripts.build_ownership_data import FOLDER, ROOT, read_jsonl, validate


class OwnershipDataTests(unittest.TestCase):
    def setUp(self):
        self.groups = {name: read_jsonl(FOLDER / f"{name}.jsonl")
                       for name in ("train", "dev", "reserved", "regression")}
        self.history = read_jsonl(ROOT / "data/v0.2/train.jsonl")

    def test_frozen_hashes_counts_and_construction_separation(self):
        manifest = json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8"))
        for name, digest in manifest["sha256"].items():
            self.assertEqual(hashlib.sha256((FOLDER / name).read_bytes()).hexdigest(), digest)
        self.assertEqual({k: len(v) for k, v in self.groups.items()}, manifest["counts"])
        validate(self.groups, self.history)

    def test_new_words_cannot_hide_reserved_pattern_leakage(self):
        groups = copy.deepcopy(self.groups)
        groups["train"][0].update(source="Return the whistle that belongs to her.",
                                  prompt="Rewrite politely: Return the whistle that belongs to her.")
        with self.assertRaisesRegex(ValueError, "Reserved construction"):
            validate(groups, self.history)

    def test_reserved_labels_must_match_the_actual_construction(self):
        groups = copy.deepcopy(self.groups)
        groups["reserved"][0]["source"] = "Return her whistle."
        with self.assertRaisesRegex(ValueError, "declared construction"):
            validate(groups, self.history)

    def test_training_targets_are_complete_and_assistant_only(self):
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION)
        for row in self.groups["train"] + self.groups["dev"]:
            encoded = encode_example(tokenizer, row)
            target = encoded["labels"][0]
            self.assertTrue((target == -100).any())
            self.assertEqual(tokenizer.decode(target[target != -100], skip_special_tokens=True).strip(), row["response"])


if __name__ == "__main__":
    unittest.main()
