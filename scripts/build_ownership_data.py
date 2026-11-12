"""Create a fixed ownership experiment with entire constructions reserved for evaluation."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/ownership-v1"
PATTERNS = {
    "relative_owner": r"\bthat belongs to\b",
    "contrast_owner": r",\s*not (?:mine|yours|his|hers|ours|theirs)\b",
    "coordinated_owners": r"\b(?:my|your|his|her|our|their)\s+\w+\s+and\s+(?:my|your|his|her|our|their)\b",
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def polite(sentence):
    if sentence.startswith("Don't "):
        return "Please do not " + sentence[6:]
    if sentence.startswith("Do not "):
        return "Please do not " + sentence[7:]
    return "Could you please " + sentence[0].lower() + sentence[1:-1] + "?"


def row(identifier, family, sentence, split):
    return {"id": identifier, "family": family, "split": split, "source": sentence,
            "prompt": "Rewrite politely: " + sentence, "response": polite(sentence)}


def validate(groups, historical):
    names = list(groups)
    for name, rows in groups.items():
        for field in ("id", "prompt"):
            values = [r[field].strip().casefold() for r in rows]
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate {field} in {name}")
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            for field in ("source", "prompt"):
                a = {r.get(field, r["prompt"]).strip().casefold() for r in groups[first]}
                b = {r.get(field, r["prompt"]).strip().casefold() for r in groups[second]}
                if a & b:
                    raise ValueError(f"{field} overlap between {first} and {second}")
    for example in [*groups["train"], *groups["dev"], *historical]:
        text = " ".join(str(example.get(k, "")) for k in ("source", "prompt", "response"))
        if any(re.search(pattern, text, re.I) for pattern in PATTERNS.values()):
            raise ValueError("Reserved construction found in training/history/development")
    for example in groups["reserved"]:
        if not re.search(PATTERNS[example["family"]], example["source"], re.I):
            raise ValueError("Reserved example does not match its declared construction")
    for example in groups["reserved"] + groups["dev"]:
        if any(example["source"].casefold() in " ".join(str(old.get(k, "")) for k in ("source", "prompt", "response")).casefold()
               for old in historical):
            raise ValueError("Reserved/development source found in historical training")


def build():
    train = []
    owners = ["my", "your", "his", "her"]
    objects = ["scarf", "basket", "camera", "ladder", "spoon", "map", "suitcase", "towel"]
    for i, owner in enumerate(owners):
        for j, obj in enumerate(objects):
            n = i * len(objects) + j + 1
            verb = ["Bring", "Return", "Clean", "Collect"][j % 4]
            recipient = ["her", "him", "me", "us"][(j + i) % 4]
            for family, source in [
                ("simple_owner", f"{verb} {owner} {obj}."),
                ("transfer_to", f"Send {owner} {obj} to {recipient}."),
                ("lend_to_me", f"Lend me {owner} {obj}."),
                ("negative_lend", f"Don't lend me {owner} {obj}."),
            ]:
                train.append(row(f"{family}-{n:02d}", family, source, "train"))
    legacy = read_jsonl(ROOT / "data/train.jsonl")
    previous = read_jsonl(ROOT / "data/v0.2/train.jsonl")
    # All original starter examples plus 16 grammar sources (two variants each).
    grammar = [r for r in previous if r.get("category") == "grammar"][:32]
    for n, old in enumerate([*legacy, *grammar], 1):
        train.append({**old, "id": f"replay-{n:02d}", "family": "replay", "split": "train"})
    dev = []
    for i, owner in enumerate(owners):
        obj = ["manual", "folder", "jacket", "receipt"][i]
        for family, source in [
            ("simple_owner", f"Return {owner} {obj}."),
            ("transfer_to", f"Send {owner} {obj} to {['him','her','us','me'][i]}."),
            ("lend_to_me", f"Lend me {owner} {obj}."),
            ("negative_lend", f"Don't lend me {owner} {obj}."),
        ]:
            dev.append(row(f"dev-{family}-{i+1}", family, source, "dev"))
    reserved = []
    for i, (obj, owner) in enumerate(zip(
        ["parcel", "badge", "helmet", "wallet", "pencil", "coat", "plate", "bottle"],
        ["me", "you", "him", "her", "us", "them", "Nora", "Tariq"]), 1):
        reserved.append(row(f"relative-{i:02d}", "relative_owner", f"Return the {obj} that belongs to {owner}.", "reserved"))
    contrasts = [("my", "yours"), ("your", "mine"), ("his", "hers"), ("her", "his"),
                 ("our", "theirs"), ("their", "ours"), ("my", "hers"), ("your", "his")]
    for i, ((owner, excluded), obj) in enumerate(zip(contrasts,
            ["parcel", "badge", "helmet", "wallet", "pencil", "coat", "plate", "bottle"]), 1):
        reserved.append(row(f"contrast-{i:02d}", "contrast_owner", f"Return {owner} {obj}, not {excluded}.", "reserved"))
    pairs = [("my", "your"), ("your", "my"), ("his", "her"), ("her", "his"),
             ("our", "their"), ("their", "our"), ("my", "her"), ("your", "his")]
    for i, (first, second) in enumerate(pairs, 1):
        a, b = [("parcel", "badge"), ("helmet", "wallet"), ("pencil", "coat"), ("plate", "bottle")][(i-1) % 4]
        reserved.append(row(f"coordinated-{i:02d}", "coordinated_owners", f"Return {first} {a} and {second} {b}.", "reserved"))
    regressions = json.loads((ROOT / "data/community/2026-11-10-prompt-rule.json").read_text(encoding="utf-8"))["cases"]
    regression_rows = [row(c["id"], "known_regression", c["sentence"], "regression") for c in regressions]
    groups = {"train": train, "dev": dev, "reserved": reserved, "regression": regression_rows}
    validate(groups, previous)
    return groups


def main():
    if FOLDER.exists():
        raise SystemExit("Experiment data already exists; preserve the frozen files.")
    groups = build()
    FOLDER.mkdir(parents=True)
    hashes = {}
    for name, rows in groups.items():
        path = FOLDER / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "date": "2026-11-12", "license": "Apache-2.0", "provenance": "AI-authored synthetic examples; no independent human review. Public feedback cases are evaluation only.",
        "counts": {k: len(v) for k, v in groups.items()}, "new_training_sources": 128, "replay_requests": 64,
        "reserved_constructions": PATTERNS, "sha256": hashes,
        "historical_training_audit": "Reserved constructions absent from candidate1's full supervised training data and the new train/dev sets. No claim about the base model's pretraining exposure.",
        "evaluation_policy": "Freeze the data and 384-step run before training. Compare candidate1 and the one new candidate on reserved patterns only after training; do not tune on their outputs. Report regressions, familiar-pattern dev, and reserved-pattern results separately.",
    }
    (FOLDER / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
