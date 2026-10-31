"""Review gate (layer C): turn a fully reviewed discovery result into resolver evidence.

  python skills/capability-resolver/scripts/review_gate.py --discovery DISCOVERY.json \
      --reviews REVIEWS.json [--out EVIDENCE.json]

REVIEWS.json is a list of {"candidate_id", "verdict": ADEQUATE|PARTIAL|INADEQUATE, "reason",
"adequate_for"?} written by a human (or an agent under human review), one per candidate.

A discovery result is evidence of a search only once every candidate has been reviewed: an
unreviewed candidate list must not count as "searched, nothing adequate" (that would let the
resolver reach BUILD). So this gate refuses any discovery that is unavailable, or that has a
candidate with no review, a review for an unknown candidate, a duplicate review, or a review
without a verdict and reason. The output is {"search_record", "evaluated_options"} to merge into a
resolver request. Works on the output of every external discovery adapter
(adapters.IMPLEMENTED_EXTERNAL_ADAPTERS: github_adapter.py, plugin_discovery.py). It does not decide
anything, register, install or connect anything.

This gate is the ONLY component that creates resolver evidence from external discovery (GA-01).
Its search_record carries a "review_gate" attestation ({version, adapters, candidates, reviewed});
the resolver refuses a search_record that names an external adapter without one. merge_evidence()
combines several gate outputs, and optionally manually recorded evidence, into one request.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adapters import IMPLEMENTED_EXTERNAL_ADAPTERS  # noqa: E402

GATE_VERSION = "1.0"
VERDICTS = ("ADEQUATE", "PARTIAL", "INADEQUATE")
SEARCHED = ("OK", "NONE_FOUND")


class ReviewError(ValueError):
    pass


def _candidate_key(c: dict):
    return c.get("candidate_id") or c.get("id")


def _candidate_source(c: dict, adapter: str) -> str:
    for key in ("source_reference", "url"):
        if isinstance(c.get(key), str) and c[key] not in ("", "UNKNOWN"):
            return c[key]
    catalog_id = c.get("catalog_id") if c.get("catalog_id") not in (None, "UNKNOWN") else None
    return f"{adapter}: {c.get('source', 'catalog')} entry {catalog_id or c.get('name')}"


def to_resolver_evidence(discovery: dict, reviews: list[dict]) -> dict:
    adapter = discovery.get("adapter")
    if adapter not in IMPLEMENTED_EXTERNAL_ADAPTERS:
        raise ReviewError(f"discovery adapter {adapter!r} is not an implemented external discovery "
                          f"adapter {IMPLEMENTED_EXTERNAL_ADAPTERS}")
    if "search_record" in discovery or "evaluated_options" in discovery:
        raise ReviewError("discovery output already carries resolver evidence; external adapters "
                          "must emit discovery-level output only (GA-01)")
    status = discovery.get("status")
    if status not in SEARCHED:
        raise ReviewError(f"discovery status {status!r}: no search evidence "
                          f"({discovery.get('reason', 'search did not run')})")
    query = (discovery.get("github_query")
             or (discovery.get("request") or {}).get("query"))
    gap = (discovery.get("request") or {}).get("capability_gap")
    if not query or not gap:
        raise ReviewError("discovery result has no query or capability gap")
    candidates = {_candidate_key(c): c for c in discovery.get("candidates", [])}
    if None in candidates:
        raise ReviewError("a candidate has no id")
    if not isinstance(reviews, list):
        raise ReviewError("reviews must be a list")
    by_id = {}
    for r in reviews:
        cid = r.get("candidate_id") if isinstance(r, dict) else None
        if cid not in candidates:
            raise ReviewError(f"review for {cid!r}, which is not a candidate of this discovery")
        if cid in by_id:
            raise ReviewError(f"more than one review for {cid}")
        if r.get("verdict") not in VERDICTS or not str(r.get("reason", "")).strip():
            raise ReviewError(f"review for {cid} needs a verdict in {VERDICTS} and a reason")
        by_id[cid] = r
    missing = [cid for cid in candidates if cid not in by_id]
    if missing:
        raise ReviewError(f"unreviewed candidate(s): {', '.join(missing)}; every candidate needs a "
                          "verdict before the discovery counts as a search")
    options = []
    for cid, c in candidates.items():
        r = by_id[cid]
        opt = {"id": cid, "source": _candidate_source(c, adapter), "verdict": r["verdict"],
               "reason": r["reason"].strip()}
        if r.get("adequate_for"):
            opt["adequate_for"] = list(r["adequate_for"])
        options.append(opt)
    counts = {v: sum(o["verdict"] == v for o in options) for v in VERDICTS}
    summary = (f"{adapter} search for gap {gap} via {discovery.get('backend', 'github api')}: "
               + (f"{len(options)} candidate(s), all reviewed ("
                  + ", ".join(f"{n} {v}" for v, n in counts.items()) + ")."
                  if options else "NONE_FOUND (the search returned no candidates)."))
    return {"search_record": {"sources": [adapter], "queries": [query], "summary": summary,
                              "review_gate": {"version": GATE_VERSION, "adapters": [adapter],
                                              "candidates": len(candidates),
                                              "reviewed": len(options)}},
            "evaluated_options": options}


def merge_evidence(*parts: dict) -> dict:
    """Combine gate outputs (and manually recorded {search_record, evaluated_options}) into one."""
    if not parts:
        raise ReviewError("nothing to merge")
    sources, queries, summaries, options, ids = [], [], [], [], set()
    adapters, candidates, reviewed = [], 0, 0
    for part in parts:
        record = part.get("search_record") if isinstance(part, dict) else None
        if not isinstance(record, dict):
            raise ReviewError("every part needs a search_record")
        gate = record.get("review_gate")
        external = [s for s in record.get("sources", []) if s in IMPLEMENTED_EXTERNAL_ADAPTERS]
        if external and not isinstance(gate, dict):
            raise ReviewError(f"part from {external} did not come through the review gate")
        if isinstance(gate, dict):
            adapters += [a for a in gate.get("adapters", []) if a not in adapters]
            candidates += gate.get("candidates", 0)
            reviewed += gate.get("reviewed", 0)
        sources += [s for s in record.get("sources", []) if s not in sources]
        queries += record.get("queries", [])
        summaries.append(record.get("summary", ""))
        for opt in part.get("evaluated_options", []):
            if opt.get("id") in ids:
                raise ReviewError(f"evaluated option {opt.get('id')!r} appears in more than one part")
            ids.add(opt.get("id"))
            options.append(opt)
    record = {"sources": sources, "queries": queries, "summary": " | ".join(s for s in summaries if s)}
    if adapters:
        record["review_gate"] = {"version": GATE_VERSION, "adapters": adapters,
                                 "candidates": candidates, "reviewed": reviewed}
    return {"search_record": record, "evaluated_options": options}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--discovery", type=Path, required=True)
    ap.add_argument("--reviews", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    try:
        evidence = to_resolver_evidence(json.loads(args.discovery.read_text("utf-8")),
                                        json.loads(args.reviews.read_text("utf-8")))
    except ReviewError as exc:
        print(f"REVIEW GATE: REFUSED: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
