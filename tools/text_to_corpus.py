"""Reconstruct the evidence blocks from the faithful anchored input text without a PDF dependency."""
import argparse
import json
from pathlib import Path
import re


def convert(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    header = dict(re.findall(r"^(SOURCE_ID|TITLE|DOI|LICENSE|SOURCE_SHA256): (.+)$", text, re.M))
    anchors = list(re.finditer(r"^\[([^:\n]+):([^;\n]+); PDF page (\d+)\]\n", text, re.M))
    if not anchors or len(header) != 5:
        raise ValueError("Missing anchored original text header")
    blocks = []
    for i, anchor in enumerate(anchors):
        if anchor.group(1) != header["SOURCE_ID"]:
            raise ValueError("Source mismatch")
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(text)
        blocks.append({"block_id": anchor.group(2), "pdf_page": int(anchor.group(3)), "text": text[anchor.end():end].strip()})
    return {"schema_version": "paperscope-corpus/1.0", "source_id": header["SOURCE_ID"], "source_sha256": header["SOURCE_SHA256"],
            "title": header["TITLE"], "doi": header["DOI"], "license": header["LICENSE"], "blocks": blocks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refuse to overwrite an existing corpus")
    args.output.write_text(json.dumps(convert(args.input), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
