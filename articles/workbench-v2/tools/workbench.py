"""Local evidence workbench. Integrity, lexical retrieval and human review remain distinct."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys
try:
    import integrity
except ModuleNotFoundError:
    import paperscope as integrity

VERSION = "paperscope-workbench/2.0-prototype"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bounded(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Input path escapes the declared project")
    return path


def load_corpora(root):
    paths = sorted((root / "materials/corpus").glob("*.json"))
    corpora = [read(bounded(root, path.relative_to(root))) for path in paths]
    if not corpora:
        import text_to_corpus
        sources = read(root / "materials/sources.json")["sources"]
        corpora = [text_to_corpus.convert(bounded(root, item["path"])) for item in sources if item.get("kind") == "anchored_text"]
    if not corpora:
        raise ValueError("No corpus JSON or registered anchored text input")
    if len({item["source_id"] for item in corpora}) != len(corpora):
        raise ValueError("Duplicate source identifiers")
    for corpus in corpora:
        issues = integrity.corpus_errors(corpus)
        if issues:
            raise ValueError("Invalid corpus: " + "; ".join(issues))
    return {item["source_id"]: item for item in corpora}


def source_checks(root):
    results = []
    for item in read(root / "materials/sources.json")["sources"]:
        path = bounded(root, item["path"])
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        results.append({"source_id": item["source_id"], "path": item["path"],
                        "expected_sha256": item["sha256"], "actual_sha256": actual,
                        "matches_registered_source": actual == item["sha256"]})
    return results


def audit(root):
    corpora = load_corpora(root)
    manifest = read(root / "manifest.json")
    metrics_path = root / "evaluation/results/run-summary.json"
    metrics = {item["run_id"]: item for item in read(metrics_path)["rows"]} if metrics_path.exists() else {}
    runs = []
    for item in manifest["runs"]:
        rid = item["id"]
        run_root = bounded(root, f"runs/{rid}")
        claims = read(run_root / "claims.json")
        selected = [corpora[sid] for sid in claims["source_ids"]]
        errors = integrity.claims_errors(selected, claims)
        errors += integrity.comparison_errors(run_root / "comparison.csv", claims)
        evidence = [ev for claim in claims["claims"] for ev in claim["evidence"]]
        record = {"run_id": rid, "case_id": item["case_id"],
                  "condition": metrics.get(rid, {}).get("condition", item.get("condition")),
                  "claims_count": len(claims["claims"]), "evidence_count": len(evidence),
                  "integrity_passed": not errors, "errors": errors,
                  "semantic_support_verified": False, "claims": claims["claims"],
                  "metrics": metrics.get(rid, {}),
                  "claims_file_sha256": hashlib.sha256((run_root / "claims.json").read_bytes()).hexdigest()}
        runs.append(record)
    sources = source_checks(root)
    return {"version": VERSION, "runs": runs, "source_file_checks": sources,
            "all_integrity_checks_passed": all(item["integrity_passed"] for item in runs),
            "all_registered_sources_match": all(item["matches_registered_source"] for item in sources),
            "semantic_support_verified": False, "competition_score": None,
            "scope": "Registered-file hashes, literal citations, comparison references, and authentic recorded metrics. Not a semantic truth oracle or new model experiment."}


ALIASES = {"划分": "split splitting", "泛化": "generalization extrapolation", "未见": "unseen",
           "化学体系": "chemical chemistry", "回归": "regression", "误差": "error mae",
           "稳定性": "stability", "勘误": "correction corrected", "基线": "baseline",
           "不确定性": "uncertainty", "组成": "composition", "筛选": "screening discovery"}


def words(text):
    return re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", text.lower())


def search(corpora, query, limit=8):
    expanded = query + " " + " ".join(value for key, value in ALIASES.items() if key in query)
    terms = set(words(expanded))
    if not terms:
        return {"query": query, "expanded_query": expanded, "results": [], "method": "literal term matching; no semantic inference"}
    blocks = [(sid, block, Counter(words(block["text"]))) for sid, corpus in corpora.items() for block in corpus["blocks"]]
    frequencies = {term: sum(term in counts for _, _, counts in blocks) for term in terms}
    results = []
    for sid, block, counts in blocks:
        matched = sorted(term for term in terms if term in counts)
        if not matched:
            continue
        score = sum((1 + math.log(counts[term])) * (1 + math.log((len(blocks) + 1) / (frequencies[term] + 1))) for term in matched)
        score /= math.sqrt(max(1, sum(counts.values())))
        results.append({"source_id": sid, "block_id": block["block_id"], "pdf_page": block["pdf_page"],
                        "matched_terms": matched, "lexical_score": round(score, 6), "text": block["text"]})
    results.sort(key=lambda item: (-item["lexical_score"], item["source_id"], item["block_id"]))
    return {"query": query, "expanded_query": expanded.strip(), "results": results[:limit],
            "method": "deterministic term-frequency/rarity weighting with explicit bilingual query aliases; ranking is not semantic support"}


def probes(root):
    """Explicit synthetic mutations, never represented as actual model mistakes."""
    corpora = load_corpora(root)
    original = read(root / "runs/R02/claims.json")
    selected = [corpora[sid] for sid in original["source_ids"]]
    variants = []
    def record(name, document, expected, interpretation):
        errors = integrity.claims_errors(selected, document)
        variants.append({"probe": name, "synthetic": name != "unchanged_actual_R02", "integrity_passed": not errors,
                         "expected_integrity_passed": expected, "matches_expected": (not errors) == expected,
                         "errors": errors, "interpretation": interpretation})
    record("unchanged_actual_R02", original, True, "Unchanged genuine output is the control.")
    bad = copy.deepcopy(original)
    bad["claims"][0]["evidence"][0]["quote"] += " THIS_SENTENCE_IS_A_SYNTHETIC_MUTATION_7351"
    record("changed_quote", bad, False, "Literal corruption must be rejected.")
    bad = copy.deepcopy(original)
    bad["claims"][0]["evidence"][0]["source_id"] = "nonexistent-source"
    record("wrong_source", bad, False, "A real quote cannot be attributed to an undeclared source.")
    bad = copy.deepcopy(original)
    bad["claims"][0].update(kind="unknown", verdict="supported")
    record("unknown_marked_supported", bad, False, "An internally inconsistent output contract must fail.")
    bad = copy.deepcopy(original)
    bad["claims"][0]["statement"] = "SYNTHETIC FALSE CLAIM: CrabNet strictly beats every comparison model on all 28 datasets and proves reliable screening in unseen chemical systems."
    record("wrong_statement_with_unchanged_real_quote", bad, True,
           "A deliberately overstated statement still passes literal checks. This is a demonstrated semantic blind spot, not a genuine model error or a claim of semantic verification.")
    return {"version": VERSION, "source_run": "R02", "real_model_rerun": False,
            "protocol": "Explicit deterministic tool probes authored after v1, not a preregistered model benchmark.",
            "all_expected_behaviours_observed": all(item["matches_expected"] for item in variants), "probes": variants}


STYLE = """body{margin:0;background:#f3f5f7;color:#172735;font:15px/1.65 system-ui,'Microsoft YaHei',sans-serif}main{max-width:1180px;margin:auto;padding:36px 24px}h1{font-size:34px;letter-spacing:-1px;margin:0}h2{font-size:22px}header{border-bottom:1px solid #ccd7dc;padding-bottom:20px}.eyebrow{color:#087c78;font-weight:700;letter-spacing:2px}.sub{color:#536977;max-width:880px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}.card,.claim{background:white;border:1px solid #dce3e7;border-radius:10px;padding:18px;margin:12px 0}.number{font-size:29px;font-weight:700}.muted{font-size:13px;color:#61727d}.badge{display:inline-block;padding:2px 9px;background:#e7f4ef;color:#176542;border-radius:20px;font-size:12px}.pending{background:#fff0cf;color:#825d00}.bad{background:#fae4e4;color:#9a2530}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 0;position:sticky;top:0;background:#f3f5f7;z-index:1}input,select,button,textarea{font:inherit;border:1px solid #b8c8d0;border-radius:6px;padding:9px;background:white}input{flex:1;min-width:200px}button{background:#087c78;color:white;cursor:pointer}textarea{width:96%;min-height:65px}table{border-collapse:collapse;width:100%;background:white}td,th{text-align:left;border-bottom:1px solid #e0e6e9;padding:9px}th{background:#edf2f4}blockquote{border-left:3px solid #099b92;margin:12px 0;padding:5px 15px;background:#f0f8f7;white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer;color:#087c78}.context{white-space:pre-wrap;color:#3b5261}.claim h3{margin:5px 0 9px}.hidden{display:none!important}footer{margin:35px 0;color:#536977}@media(max-width:750px){.grid{grid-template-columns:1fr 1fr}main{padding:20px 12px}h1{font-size:26px}.tablewrap{overflow:auto}}"""
SCRIPT = """const q=document.querySelector('#filter'),r=document.querySelector('#run');function filter(){for(const c of document.querySelectorAll('.claim'))c.classList.toggle('hidden',!(c.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!r.value||c.dataset.run===r.value)))}q.addEventListener('input',filter);r.addEventListener('change',filter);document.querySelector('#export').addEventListener('click',()=>{const reviews=[...document.querySelectorAll('.review')].filter(t=>t.value.trim()).map(t=>({run_id:t.dataset.run,claim_id:t.dataset.claim,claims_file_sha256:t.dataset.sha256,note:t.value.trim()}));const b=new Blob([JSON.stringify({schema_version:'paperscope-human-notes/1',source:'user-entered notes; not automatic semantic verification',reviews},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='paperscope-review-notes.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)});"""


def render(report, corpora):
    escape = lambda value: html.escape(str(value), quote=True)
    blocks = {(sid, block["block_id"]): block for sid, corpus in corpora.items() for block in corpus["blocks"]}
    runs = report["runs"]
    claim_count = sum(item["claims_count"] for item in runs)
    evidence_count = sum(item["evidence_count"] for item in runs)
    good = sum(item["integrity_passed"] for item in runs)
    source_good = sum(item["matches_registered_source"] for item in report["source_file_checks"])
    parts = ["<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'\">",
             "<title>PaperScope 证据核查工作台</title><style>" + STYLE + "</style><main>",
             "<header><div class='eyebrow'>PAPERSCOPE / EVIDENCE WORKBENCH V2</div><h1>从一句结论，回到它的证据与条件</h1>",
             "<p class='sub'>原文、真实模型输出与人工判断分开。此页在本地工作，不向服务器发送论文或审阅备注。绿色仅表示机械检查通过；语义支持仍待阅读者判断。</p></header><div class='grid'>"]
    for value, label in [(len(runs), "真实既有运行"), (claim_count, "待核查主张"), (evidence_count, "原文引用"), (f"{good}/{len(runs)}", "机械检查通过")]:
        parts.append(f"<div class='card'><div class='number'>{escape(value)}</div><div class='muted'>{label}</div></div>")
    parts.append(f"</div><p><span class='badge'>登记文件哈希 {source_good}/{len(report['source_file_checks'])} 一致</span> <span class='badge pending'>语义支持：未自动验证</span> <span class='badge pending'>不是竞赛评分器</span></p><h2>先看真实运行</h2><p class='muted'>A：原文任务；B：新论文；C：显式构造的缺失材料。需核对图表时请打开原始PDF或随包关键页图，按每项引用的PDF页序定位。</p><div class='tablewrap'><table><tr><th>运行</th><th>案例</th><th>条件</th><th>耗时/秒</th><th>工具</th><th>输出token</th><th>主张/引用</th></tr>")
    for run in runs:
        metric = run["metrics"]
        parts.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in [run["run_id"], run["case_id"], run["condition"], metric.get("duration_seconds", "未提供"), metric.get("tool_calls", "未提供"), metric.get("output_tokens", "未提供"), f"{run['claims_count']} / {run['evidence_count']}"]) + "</tr>")
    options = "".join(f"<option value='{escape(run['run_id'])}'>{escape(run['run_id'])}</option>" for run in runs)
    parts.append("</table></div><h2>逐项核查</h2><div class='toolbar'><input id='filter' aria-label='过滤主张与原文' placeholder='输入数字、指标、条件或主张关键词'><select id='run' aria-label='选择运行'><option value=''>全部运行</option>" + options + "</select><button id='export'>下载我的审阅备注</button></div>")
    for run in runs:
        for claim in run["claims"]:
            rid, cid = run["run_id"], claim["id"]
            parts.append(f"<article class='claim' data-run='{escape(rid)}'><div class='muted'>{escape(rid)} · {escape(cid)} · {escape(claim['kind'])} · 模型判断：{escape(claim['verdict'])}</div><h3>{escape(claim['statement'])}</h3><p>{escape(claim['reasoning'])}</p>")
            for evidence in claim["evidence"]:
                sid, bid = evidence["source_id"], evidence["block_id"]
                if bid.startswith(sid + ":"):
                    bid = bid[len(sid) + 1:]
                block = blocks.get((sid, bid), {})
                parts.append(f"<div class='muted'>{escape(sid)} · {escape(bid)} · PDF页序 {escape(block.get('pdf_page', '未知'))}</div><blockquote>{escape(evidence['quote'])}</blockquote><details><summary>展开完整原文块，检查限定词与上下文</summary><p class='context'>{escape(block.get('text', '位置未找到'))}</p></details>")
            parts.append(f"<p class='muted'>请核对：引用支持的是该结论，还是更窄的事实？条件、单位和量词是否保留？</p><textarea class='review' data-run='{escape(rid)}' data-claim='{escape(cid)}' data-sha256='{escape(run['claims_file_sha256'])}' aria-label='审阅备注 {escape(rid)} {escape(cid)}' placeholder='记录你的判断及依据；保存请点上方下载按钮'></textarea></article>")
    parts.append("<footer>本页读取既有真实记录生成。搜索过滤不是证据充分性判断；作者侧检查不是独立科学复现。论文与第三方材料沿用原始许可。</footer></main><script>" + SCRIPT + "</script></html>")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["audit", "search", "probes"])
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--query", default="")
    parser.add_argument("--source", action="append", help="Explicit corpus scope for lexical retrieval; repeatable")
    args = parser.parse_args()
    root = args.project.resolve()
    if args.command == "search":
        if not args.source:
            raise ValueError("Choose --source explicitly to avoid mixing originals and synthetic variants")
        corpora = load_corpora(root)
        print(json.dumps(search({sid: corpora[sid] for sid in args.source}, args.query), ensure_ascii=False, indent=2))
        return
    report = audit(root) if args.command == "audit" else probes(root)
    if args.out is None:
        raise ValueError("An explicit new output directory is required")
    if args.out.exists():
        raise ValueError("Refusing to overwrite previous generated evidence")
    args.out.mkdir(parents=True)
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.command == "audit":
        (args.out / "workbench.html").write_text(render(report, load_corpora(root)), encoding="utf-8")
        print(json.dumps({"runs": len(report["runs"]), "claims": sum(run["claims_count"] for run in report["runs"]),
                          "integrity_passed": report["all_integrity_checks_passed"], "registered_sources_match": report["all_registered_sources_match"], "semantic_support_verified": False}))
    else:
        print(json.dumps({"explicit_tool_probes": len(report["probes"]), "all_expected_behaviours_observed": report["all_expected_behaviours_observed"], "real_model_rerun": False}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
