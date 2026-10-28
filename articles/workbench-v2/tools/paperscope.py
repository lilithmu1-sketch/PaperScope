"""Offline evidence integrity checks; never a semantic or competition grader."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def corpus_errors(corpus: dict) -> list[str]:
    if not isinstance(corpus, dict):
        return ["corpus must be an object"]
    errors = []
    for key in ("source_id", "source_sha256", "blocks"):
        if key not in corpus:
            errors.append(f"missing {key}")
    if not isinstance(corpus.get("source_id"), str) or not corpus.get("source_id"):
        errors.append("source_id must be nonempty text")
    if not re.fullmatch(r"[0-9a-f]{64}", str(corpus.get("source_sha256", ""))):
        errors.append("invalid source_sha256")
    blocks = corpus.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        return errors + ["blocks must be a nonempty array"]
    seen = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            errors.append(f"block {index} must be an object")
            continue
        bid = block.get("block_id")
        if not isinstance(bid, str) or not bid:
            errors.append(f"block {index}: invalid block_id")
        elif bid in seen:
            errors.append(f"duplicate block_id: {bid}")
        else:
            seen.add(bid)
        if type(block.get("pdf_page")) is not int or block["pdf_page"] < 1:
            errors.append(f"block {index}: invalid PDF page")
        if not isinstance(block.get("text"), str) or not block.get("text", "").strip():
            errors.append(f"block {index}: empty text")
    return errors


def claims_errors(corpora: list[dict], document: dict) -> list[str]:
    errors = []
    sources = {}
    for corpus in corpora:
        issues = corpus_errors(corpus)
        if issues:
            errors.extend(issues)
            continue
        sid = corpus["source_id"]
        if sid in sources:
            errors.append(f"duplicate corpus source: {sid}")
        sources[sid] = {b["block_id"]: b for b in corpus["blocks"]}
    if not isinstance(document, dict):
        return errors + ["claims document must be an object"]
    if document.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    declared = document.get("source_ids")
    if not isinstance(declared, list) or not declared or not all(isinstance(x, str) for x in declared):
        return errors + ["source_ids must be a nonempty array of strings"]
    if len(declared) != len(set(declared)):
        errors.append("duplicate source_ids")
    if set(declared) - set(sources):
        errors.append("source_ids contains unknown corpus")
    claims = document.get("claims")
    if not isinstance(claims, list) or not 1 <= len(claims) <= 30:
        return errors + ["claims must contain 1..30 items"]
    seen = set()
    for i, claim in enumerate(claims):
        label = f"claim[{i}]"
        if not isinstance(claim, dict):
            errors.append(f"{label}: must be an object")
            continue
        cid = claim.get("id")
        if not isinstance(cid, str) or not cid or cid in seen:
            errors.append(f"{label}: missing or duplicate id")
        else:
            seen.add(cid)
            label = cid
        for field in ("statement", "reasoning"):
            if not isinstance(claim.get(field), str) or not claim.get(field, "").strip():
                errors.append(f"{label}: {field} must be nonempty text")
        kind, verdict = claim.get("kind"), claim.get("verdict")
        if kind not in ("fact", "inference", "unknown"):
            errors.append(f"{label}: invalid kind")
        if verdict not in ("supported", "contradicted", "insufficient"):
            errors.append(f"{label}: invalid verdict")
        if kind == "unknown" and verdict != "insufficient":
            errors.append(f"{label}: unknown must be insufficient")
        evidence = claim.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{label}: evidence must be an array")
            continue
        if kind in ("fact", "inference") and not evidence:
            errors.append(f"{label}: fact/inference needs evidence")
        for ev in evidence:
            if not isinstance(ev, dict):
                errors.append(f"{label}: evidence must be an object")
                continue
            sid, bid, quote = ev.get("source_id"), ev.get("block_id"), ev.get("quote")
            if not isinstance(sid, str) or not isinstance(bid, str):
                errors.append(f"{label}: source/block identifiers must be strings")
                continue
            # Input text renders anchors as source_id:block_id. Accept that exact
            # qualification without fuzzy matching or changing the raw model output.
            if bid.startswith(sid + ":"):
                bid = bid[len(sid) + 1:]
            if sid not in declared or sid not in sources or bid not in sources[sid]:
                errors.append(f"{label}: unknown or undeclared source/block")
                continue
            if not isinstance(quote, str) or not quote.strip() or len(quote) > 2000:
                errors.append(f"{label}: quote must contain 1..2000 characters")
                continue
            body, needle = normalize(sources[sid][bid]["text"]), normalize(quote)
            if body.count(needle) != 1:
                errors.append(f"{label}: quote is absent or ambiguous in its block")
    return errors


def comparison_errors(path: Path, document: dict) -> list[str]:
    errors = []
    ids = {c["id"] for c in document.get("claims", []) if isinstance(c, dict) and isinstance(c.get("id"), str)}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = ["item", "paper_setting", "target_setting", "comparability", "evidence_ids"]
        if reader.fieldnames != required:
            return ["comparison.csv: incorrect columns/order"]
        rows = list(reader)
    if not rows:
        return ["comparison.csv: no rows"]
    for i, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"comparison.csv:{i}: incorrect column count")
            continue
        if row["comparability"] not in ("comparable", "mismatch", "unknown", "not_applicable"):
            errors.append(f"comparison.csv:{i}: invalid comparability")
        if not all(row[x].strip() for x in required[:-1]):
            errors.append(f"comparison.csv:{i}: empty required value")
        refs = {v.strip() for v in row["evidence_ids"].split(";") if v.strip()}
        if refs - ids:
            errors.append(f"comparison.csv:{i}: unknown evidence ids")
    return errors


def result(errors: list[str]) -> dict:
    return {"schema_version": "paperscope-checks/1.0", "integrity_checks_passed": not errors,
            "semantic_support_verified": False, "competition_score": None, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    corpus_cmd = sub.add_parser("check-corpus")
    corpus_cmd.add_argument("path", type=Path)
    claim_cmd = sub.add_parser("check-claims")
    claim_cmd.add_argument("--corpus", type=Path, action="append", required=True)
    claim_cmd.add_argument("--claims", type=Path, required=True)
    claim_cmd.add_argument("--comparison", type=Path)
    claim_cmd.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "check-corpus":
            report = result(corpus_errors(read_json(args.path)))
        else:
            document = read_json(args.claims)
            errors = claims_errors([read_json(p) for p in args.corpus], document)
            if args.comparison:
                errors.extend(comparison_errors(args.comparison, document))
            report = result(errors)
            if args.out:
                if args.out.exists():
                    raise ValueError("refusing to overwrite existing checks file")
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["integrity_checks_passed"] else 1
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps(result([str(error)]), ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())

