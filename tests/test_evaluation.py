"""
PII-Shield — Detection Evaluation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Measures precision, recall, and F1 for the detection engine
against the synthetic prompt test set.

Usage:
    python -m tests.test_evaluation

All test data is synthetic — no real PII is used.
"""

import json
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.engine.detector import Detector
from backend.engine.presidio_wrapper import PresidioWrapper
from backend.config import settings


def load_prompts():
    data_path = Path(__file__).parent.parent / "data" / "synthetic_prompts.json"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


def evaluate():
    """Run evaluation and print results."""
    # Initialize detector
    presidio = PresidioWrapper(
        model_name=settings.SPACY_MODEL,
        score_threshold=settings.PRESIDIO_SCORE_THRESHOLD,
    )
    presidio.load()
    detector = Detector(presidio=presidio)

    prompts = load_prompts()

    # Counters for precision/recall
    total_true_positives = 0
    total_false_positives = 0
    total_false_negatives = 0
    total_true_negatives = 0

    results = []

    for prompt in prompts:
        text = prompt["text"]
        expected_types = set(prompt["expected_entities"])
        entities = detector.detect(text)
        detected_types = set(e.entity_type for e in entities)

        # Type-level evaluation
        tp = expected_types & detected_types
        fp = detected_types - expected_types
        fn = expected_types - detected_types

        total_true_positives += len(tp)
        total_false_positives += len(fp)
        total_false_negatives += len(fn)

        # True negative: no PII expected and none detected
        if not expected_types and not detected_types:
            total_true_negatives += 1

        status = "PASS" if not fn else "MISS"
        results.append({
            "id": prompt["id"],
            "description": prompt["description"],
            "expected": sorted(expected_types),
            "detected": sorted(detected_types),
            "tp": sorted(tp),
            "fp": sorted(fp),
            "fn": sorted(fn),
            "status": status,
        })

    # Calculate metrics
    precision = (
        total_true_positives / (total_true_positives + total_false_positives)
        if (total_true_positives + total_false_positives) > 0
        else 0.0
    )
    recall = (
        total_true_positives / (total_true_positives + total_false_negatives)
        if (total_true_positives + total_false_negatives) > 0
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # Print report
    print("=" * 70)
    print("PII-Shield — Detection Evaluation Report")
    print(f"Engine: {'Presidio + Regex' if presidio.is_loaded else 'Regex-only'}")
    print(f"Model: {settings.SPACY_MODEL}")
    print(f"Test set: {len(prompts)} synthetic prompts")
    print("=" * 70)
    print()

    for r in results:
        print(f"  [{r['status']}] {r['id']} - {r['description']}")
        print(f"     Expected: {r['expected']}")
        print(f"     Detected: {r['detected']}")
        if r["fp"]:
            print(f"     False positives: {r['fp']}")
        if r["fn"]:
            print(f"     Missed: {r['fn']}")
        print()

    print("-" * 70)
    print(f"  True positives:  {total_true_positives}")
    print(f"  False positives: {total_false_positives}")
    print(f"  False negatives: {total_false_negatives}")
    print(f"  True negatives:  {total_true_negatives}")
    print()
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall:    {recall:.2%}")
    print(f"  F1 Score:  {f1:.2%}")
    print("-" * 70)

    # Return as dict for programmatic use
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": total_true_positives,
        "false_positives": total_false_positives,
        "false_negatives": total_false_negatives,
        "true_negatives": total_true_negatives,
        "per_prompt": results,
    }


if __name__ == "__main__":
    evaluate()
