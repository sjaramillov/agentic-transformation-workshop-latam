#!/usr/bin/env python3
"""Validate an observed ATX report bundle locally; never infer runtime readiness."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def verify(path, kind, expect_questions=None):
    path = Path(path)
    errors, hashes = [], {}
    if kind not in {"ara", "mod"}:
        raise ValueError("kind must be ara or mod")
    documents = {}
    for suffix in (".json", ".md", ".html", ".metadata.json"):
        artifact = path.with_suffix(suffix)
        if not artifact.is_file() or artifact.is_symlink():
            errors.append(f"Missing regular artifact: {artifact.name}")
            continue
        content = artifact.read_bytes()
        hashes[artifact.name] = hashlib.sha256(content).hexdigest()
        if not content.strip():
            errors.append(f"Empty artifact: {artifact.name}")
        if suffix.endswith(".json"):
            try:
                document = json.loads(content)
                if not isinstance(document, dict):
                    raise ValueError("Expected an object")
                documents[suffix] = document
            except (ValueError, UnicodeDecodeError) as exc:
                errors.append(f"Invalid JSON: {artifact.name}: {exc}")
    data = documents.get(".json", {})
    findings, classification = data.get("findings"), data.get("classification")
    if not isinstance(findings, list) or not all(isinstance(f, dict) for f in findings):
        errors.append("findings must be an array of objects")
        findings = []
    if not isinstance(classification, dict):
        errors.append("classification must be an object")
        classification = {}
    ids = [f.get("question_id") for f in findings]
    if any(not isinstance(i, str) or not i for i in ids):
        errors.append("Missing finding question_id")
    elif len(ids) != len(set(ids)):
        errors.append("Duplicate finding question_id")
    severities = [f.get("severity") for f in findings]
    severity = Counter(s for s in severities if isinstance(s, str))
    if len(severities) != sum(severity.values()) or set(severity) - {"High", "Medium", "Low"}:
        errors.append("Unknown severity; inspect report schema")
    for level in ("High", "Medium", "Low"):
        key = level.lower() + "_count"
        if type(classification.get(key)) is not int or classification[key] != severity[level]:
            errors.append(f"Count mismatch: {key}")
    counts = data.get("counts")
    if counts is not None:
        if not isinstance(counts, dict):
            errors.append("counts must be an object")
        else:
            expected = {s.lower(): severity[s] for s in ("High", "Medium", "Low")}
            expected["total"] = len(findings)
            for key, value in expected.items():
                if type(counts.get(key)) is not int or counts[key] != value:
                    errors.append(f"Count mismatch: counts.{key}")
    if kind == "ara":
        native = [(f.get("ara_metadata") or {}).get("native_severity")
                  for f in findings if isinstance(f.get("ara_metadata", {}), dict)]
        buckets = Counter(s for s in native if isinstance(s, str))
        names = {"BLOCKER": "blocker_count", "RISK-SAFETY": "risk_safety_count",
                 "RISK-QUALITY": "risk_quality_count", "INFO": "info_count"}
        if set(buckets) - names.keys() or sum(buckets.values()) != len(findings):
            errors.append("Unknown ARA bucket; inspect report schema")
        for bucket, key in names.items():
            if type(classification.get(key)) is not int or classification[key] != buckets[bucket]:
                errors.append(f"Count mismatch: {key}")
    check = classification.get("classification_consistency_check",
                               data.get("classification_consistency_check"))
    if isinstance(check, dict):
        check = check.get("status")
    if check is not None and check != "consistent":
        errors.append("Report declares unresolved classification consistency")
    if expect_questions is not None:
        evaluations = data.get("evaluations", [])
        if not isinstance(evaluations, list) or not all(isinstance(e, dict) for e in evaluations):
            errors.append("evaluations must be an array of objects")
            evaluations = []
        covered = ids + [e.get("question_id") for e in evaluations]
        if (any(not isinstance(i, str) or not i for i in covered)
                or len(covered) != len(set(covered)) or len(covered) != expect_questions):
            errors.append("Question coverage differs from the expected rubric")
    return {"valid_bundle_and_counts": not errors, "kind": kind,
            "reported_tier": classification.get("tier"), "findings": len(findings),
            "artifact_sha256": hashes, "errors": errors,
            "runtime_validated": False, "rubric_judgments_independently_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--kind", choices=("ara", "mod"), required=True)
    parser.add_argument("--expect-questions", type=int)
    args = parser.parse_args()
    result = verify(args.report, args.kind, args.expect_questions)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid_bundle_and_counts"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
