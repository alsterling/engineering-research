"""Critic materiality gate (O-P6-03): can a critic finding still change the recommendation?

The frozen RC3 critic fires C3 (label 3) for any missed qualifying family, whatever its SOFT rank. In a
crowded category a fresh critic pass can therefore always find one more qualifying family, and the
critic/research loop never converges, also when the new candidate cannot beat the leader. The RUN and
the CRITIC stay frozen; this gate, at the selector layer, classifies every critic finding:

  MATERIAL               it could change the preferred candidate, a HARD compliance state, the
                         user-approved ranking, a safety/reliability conclusion or the evidence
                         confidence: it blocks finalization and the RUN must address it
  NON_MATERIAL           a missed candidate that also passes every HARD requirement on manufacturer
                         evidence and is strictly dominated by the leader on the G1-approved SOFT
                         ranking, with comparable evidence for both: recorded; no research loop
  INSUFFICIENT_EVIDENCE  the evidence cannot show that the finding is non-material: it blocks

Only a MISSED_QUALIFYING_CANDIDATE can ever be NON_MATERIAL. A HARD status change on the leader
(C1/C2, incorrect HARD PASS, missed HARD failure), a safety-critical requirement, a requirement
interpretation (SEMANTIC_INTERPRETATION), and any safety, reliability, manufacturer-claim or provenance
concern the RUN reports from the critic are always MATERIAL. No tie-breaker is invented: an UNKNOWN SOFT
value on a criterion that decides the order makes the finding INSUFFICIENT_EVIDENCE, unless the human's
own words say that an UNKNOWN on that criterion does not separate candidates. Standard-library Python
3.10+, no network.
"""
from __future__ import annotations

import re

MATERIAL, NON_MATERIAL, INSUFFICIENT = "MATERIAL", "NON_MATERIAL", "INSUFFICIENT_EVIDENCE"
RESOLVED = "RESOLVED"  # status only: a later clean critic pass on the current leader settled it
CLASSES = (MATERIAL, NON_MATERIAL, INSUFFICIENT)
MISSED = "MISSED_QUALIFYING_CANDIDATE"
HARD_CHANGE, HARD_STATE, SAFETY, INTERPRETATION, CONCERN = (
    "HARD_STATUS_CHANGE", "HARD_STATE_CHANGE", "SAFETY", "REQUIREMENT_INTERPRETATION", "CRITIC_CONCERN")
CONCERN_TYPES = ("SAFETY", "RELIABILITY", "HARD", "REQUIREMENT_INTERPRETATION", "MANUFACTURER_CLAIM",
                 "PROVENANCE", "EVIDENCE_QUALITY")
LOWER = re.compile(r"\b(?:minimi[sz]e\w*|min|lower|lowest|less|least|smaller|smallest|narrower|narrowest|"
                   r"shorter|shortest|cheaper|cheapest|lighter|lightest)\b", re.I)
HIGHER = re.compile(r"\b(?:maximi[sz]e\w*|max|higher|highest|more|most|greater|greatest|larger|largest|"
                    r"wider|widest|longer|longest)\b", re.I)
PRICE = re.compile(r"\b(?:price|cost|eur|usd|gbp|chf)\b|[€$£]", re.I)
SOFT_SOURCES = ("MANUFACTURER", "DERIVED")  # comparable evidence for a SOFT value; a price may be DISTRIBUTOR
UNKNOWN_WORDS = re.compile(r"\b(?:unknown|n/?a|tbd|not (?:found|stated|available|published))\b", re.I)
NOT_SEPARATE = re.compile(r"\b(?:does not|doesn't|do not|don't|cannot|can't|will not|won't|not)\s+separate", re.I)


def norm_name(text) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def norm_unit(u) -> str:
    u = str(u or "").strip().lower().replace("°", "").replace("deg", "").replace("€", "eur ").replace("$", "usd ")
    return re.sub(r"\s+", " ", u).strip()


def truthy(v) -> bool:
    return v is True or str(v).strip().upper() in ("YES", "TRUE")


# ---------------------------------------------------------------- findings from a CRITIC_RESULT

def extract(critic: dict, spec: dict, fired: list, label: int, pass_no: int, round_no: int) -> list:
    """The findings of one critic pass, normalized. fired: the enforced C1-C3 that fired."""
    safety_ids = {r.get("id") for r in (spec or {}).get("requirements") or []
                  if isinstance(r, dict) and truthy(r.get("safety_critical"))}
    leader = (critic.get("job1") or {}).get("leader")
    base = {"critic_pass": pass_no, "round": round_no, "leader": leader, "label": label,
            "status": None, "class": None, "assessments": []}
    out = []
    for i, f in enumerate((critic.get("job1") or {}).get("findings") or [], 1):
        kind = (SAFETY if f.get("requirement_id") in safety_ids else
                INTERPRETATION if f.get("finding_type") == "SEMANTIC_INTERPRETATION" else HARD_CHANGE)
        out.append({**base, "id": f"P{pass_no}-J1-{f.get('finding_id') or i}", "kind": kind,
                    "candidate": f.get("candidate") or leader, "requirement_id": f.get("requirement_id"),
                    "summary": f"{f.get('requirement_id')} {f.get('old_status')} -> {f.get('new_status')} "
                               f"({f.get('finding_type')}): {f.get('reason', '')}".strip()})
    if not out and {"C1", "C2"} & set(fired):
        out.append({**base, "id": f"P{pass_no}-HARD", "kind": HARD_STATE, "candidate": leader,
                    "summary": f"{', '.join(c for c in fired if c in ('C1', 'C2'))} fired: a HARD state changed"})
    job2 = critic.get("job2") or {}
    if "C3" in fired:
        authority = {str(e.get("id")): str(e.get("authority", "")) for e in critic.get("evidence") or []
                     if isinstance(e, dict)}
        rows = {}
        for rid, r in (job2.get("rows") or {}).items():
            refs = [str(x) for x in r.get("evidence_refs") or []]
            rows[rid] = {"status": r.get("status"), "authorities": [authority.get(x, "NOT_IN_CRITIC_EVIDENCE") for x in refs]}
        out.append({**base, "id": f"P{pass_no}-J2", "kind": MISSED,
                    "candidate_name": job2.get("exact_candidate") or job2.get("family"),
                    "family": job2.get("family"), "eligibility_class": job2.get("eligibility_class"),
                    "job2_result": job2.get("result"), "job2_rows": rows, "candidate_id": None,
                    "summary": f"missed qualifying candidate {job2.get('exact_candidate') or job2.get('family')} "
                               f"({job2.get('eligibility_class')}, {job2.get('result')})"})
    return out


def concerns(memo: dict, pass_no: int, round_no: int, leader, fired: list) -> tuple[list, list, list]:
    """(findings, caveats, limitations) from the concerns the RUN transcribes from the critic (memo.critic_concerns).

    A caveat the critic itself closed (critic_disposition CLOSED_BY_CRITIC, with the critic's quote) changes
    nothing the critic decided: it is recorded as a caveat. A process-level note that names no candidate and no
    HARD requirement (candidate null, requirement_ids []: for example a same-family critic, or the bounded Job 2
    scope) is recorded as a limitation. Both are carried into the result's unresolved risks, never dropped.
    Every other concern is a finding (CRITIC_CONCERN), assessed by assess(). Fail closed: a SAFETY or RELIABILITY
    concern, a concern without a disposition, quote or target fields, or one from a pass where C1/C2 fired is
    always a finding."""
    findings, caveats, limitations = [], [], []
    for i, c in enumerate((memo or {}).get("critic_concerns") or [], 1):
        c = c if isinstance(c, dict) else {"type": "SAFETY", "text": str(c)}
        kind = str(c.get("type", "SAFETY")).upper()
        entry = {"critic_pass": pass_no, "round": round_no, "leader": leader, "id": f"P{pass_no}-K{i}",
                 "concern_type": kind, "candidate": c.get("candidate") or leader, "target": c.get("candidate"),
                 "requirement_ids": c.get("requirement_ids"), "candidate_id": None,
                 "summary": f"{kind}: {c.get('text', '')}", "quote": c.get("quote")}
        hard_safe = kind not in ("SAFETY", "RELIABILITY") and not {"C1", "C2"} & set(fired)
        closed = (str(c.get("critic_disposition", "")).upper() == "CLOSED_BY_CRITIC" and str(c.get("quote") or "").strip()
                  and hard_safe)
        process = (hard_safe and "candidate" in c and not c.get("candidate") and c.get("requirement_ids") == []
                   and str(c.get("quote") or "").strip())
        if closed:
            caveats.append({**entry, "disposition": "CLOSED_BY_CRITIC"})
        elif process:
            limitations.append({**entry, "disposition": "PROCESS_LIMITATION"})
        else:
            findings.append({**entry, "label": None, "status": None, "class": None, "assessments": [], "kind": CONCERN})
    return findings, caveats, limitations


def match_candidate(name, candidates: list, explicit=None) -> tuple[str | None, str | None]:
    """(candidate_id, problem). The RUN's explicit mapping wins; else an unambiguous name match."""
    ids = {c["candidate_id"] for c in candidates}
    if explicit:
        return (explicit, None) if explicit in ids else (None, f"mapped candidate {explicit!r} is not in the CHECK_RESULT")
    key = norm_name(name)
    if len(key) < 4:
        return None, f"the critic's candidate {name!r} cannot be matched by name"
    hits = [c["candidate_id"] for c in candidates
            if key == norm_name(c.get("name")) or (len(norm_name(c.get("name"))) >= 4 and
                                                   (key in norm_name(c.get("name")) or norm_name(c.get("name")) in key))]
    if len(hits) == 1:
        return hits[0], None
    if not hits:
        return None, f"the critic's candidate {name!r} is not in the applied CHECK_RESULT"
    return None, f"the critic's candidate {name!r} matches several candidates {hits}: map it in memo.critic_candidate_ids"


# ---------------------------------------------------------------- the user-approved ranking

def ranking(spec: dict, g1: dict | None, user_text: str) -> tuple[list, list]:
    """The SOFT ranking criteria in the G1-approved order: [{id, prefer, unit, price, unknown_does_not_separate}]."""
    rows = {r.get("id"): r for r in (spec or {}).get("requirements") or [] if isinstance(r, dict)}
    approved = {r["id"]: r for r in (g1 or {}).get("rows") or [] if r.get("decision") == "APPROVE"}
    crits, problems = [], []
    order = (spec or {}).get("soft_priority_order")
    soft_rows = [i for i, r in rows.items() if str(r.get("class") or r.get("type") or "").upper() == "SOFT"]
    if not order:
        if len(soft_rows) > 1:
            return [], [f"the SPEC ranks by {len(soft_rows)} SOFT criteria ({', '.join(soft_rows)}) but states no "
                        "soft_priority_order: the order cannot be assumed"]
        order = soft_rows
    for entry in order:
        rid = entry.get("requirement_id") if isinstance(entry, dict) else str(entry)
        row = rows.get(rid)
        if row is None or rid not in soft_rows:
            problems.append(f"ranking criterion {rid} is not a SOFT row of the SPEC")
            continue
        if rid not in approved:
            problems.append(f"ranking criterion {rid} was not approved by the human at G1")
            continue
        prefer = str(entry.get("prefer", "")).lower() if isinstance(entry, dict) else ""
        for words in ([] if prefer in ("lower", "higher") else [str(row.get("operator", "")), str(row.get("value", ""))]):
            lo, hi = bool(LOWER.search(words)), bool(HIGHER.search(words))
            if lo != hi:
                prefer = "lower" if lo else "higher"
                break
        if prefer not in ("lower", "higher"):
            prefer = None
        if prefer is None:
            problems.append(f"ranking criterion {rid}: the comparison direction is not stated (lower or higher)")
            continue
        crits.append({"id": rid, "prefer": prefer, "unit": str(row.get("unit", "")),
                      "price": bool(PRICE.search(f"{row.get('parameter', '')} {row.get('unit', '')}")),
                      "unknown_does_not_separate": unknown_rule(rid, user_text)})
    return crits, problems


def unknown_rule(rid: str, user_text: str) -> bool:
    """True only if the human's own words say an UNKNOWN on this criterion does not separate candidates."""
    for sentence in re.split(r"(?<=[.;!?])\s+|\n+", user_text or ""):
        if re.search(rf"\b{re.escape(rid)}\b", sentence) and re.search(r"\bunknown\b", sentence, re.I) \
                and NOT_SEPARATE.search(sentence):
            return True
    return False


def soft_value(values: dict, cid: str, crit: dict) -> tuple[float | None, str]:
    """(number, note) for a candidate's SOFT value; number None when it is not comparable evidence.
    The note ends with the normalized unit in brackets; compare() requires both candidates to use the same one."""
    v = ((values or {}).get(cid) or {}).get(crit["id"])
    if v is None:
        return None, f"no {crit['id']} value recorded for {cid}"
    if not isinstance(v, dict):
        v = {"value": v}
    raw = v.get("value")
    if raw is None or (isinstance(raw, str) and (UNKNOWN_WORDS.search(raw) or not raw.strip())):
        return None, f"{crit['id']} UNKNOWN for {cid}"
    found = re.search(r"-?\d+(?:[.,]\d+)?", str(raw)) if not isinstance(raw, (int, float)) else None
    if not isinstance(raw, (int, float)) and not found:
        return None, f"{crit['id']} value {raw!r} for {cid} is not a number"
    num = float(raw) if isinstance(raw, (int, float)) else float(found.group(0).replace(",", "."))
    source = str(v.get("source") or v.get("authority") or "").upper()
    allowed = SOFT_SOURCES + (("DISTRIBUTOR", "RETAILER", "RESELLER") if crit["price"] else ())
    if not source.startswith(allowed):
        return None, f"{crit['id']} = {raw} for {cid} rests on {source or 'no stated source'} (not comparable evidence)"
    unit, spec_unit = norm_unit(v.get("unit") or crit["unit"]), norm_unit(crit["unit"])
    head = re.split(r"[^a-z0-9/%]+", unit)[0] if unit else ""
    if spec_unit and unit and head != spec_unit and unit != spec_unit:
        return None, f"{crit['id']} for {cid} is in {unit!r}, the SPEC ranks in {crit['unit']!r}"
    return num, f"{crit['id']} {num:g} {v.get('unit') or crit['unit']}".strip() + f" ({source.split()[0]}) [{unit}]"


def compare(leader: str, cand: str, crits: list, values: dict) -> tuple[str, list]:
    """Lexicographic comparison on the approved ranking: DOMINATED, BETTER, TIE or INDETERMINATE."""
    reasons = []
    for c in crits:
        lv, ln = soft_value(values, leader, c)
        cv, cn = soft_value(values, cand, c)
        if lv is None or cv is None:
            if c["unknown_does_not_separate"]:
                reasons.append(f"{c['id']}: {ln if lv is None else cn}; per the human's rule an UNKNOWN {c['id']} "
                               "does not separate the candidates")
                continue
            reasons.append(f"{c['id']} decides the order and {ln if lv is None else cn}: cannot show that {cand} "
                           f"does not outrank {leader} (no tie-breaker is invented)")
            return "INDETERMINATE", reasons
        if ln.rsplit("[", 1)[-1] != cn.rsplit("[", 1)[-1]:
            reasons.append(f"{c['id']} is not on the same basis for both: {leader} {ln}, {cand} {cn} (not comparable)")
            return "INDETERMINATE", reasons
        if lv == cv:
            reasons.append(f"{c['id']} tie: {leader} {ln}, {cand} {cn}")
            continue
        better = cv < lv if c["prefer"] == "lower" else cv > lv
        reasons.append(f"{c['id']} ({c['prefer']} ranks first): {leader} {ln}, {cand} {cn}")
        return ("BETTER" if better else "DOMINATED"), reasons
    return "TIE", reasons


# ---------------------------------------------------------------- assessment

def assess_missed(f: dict, ctx: dict) -> tuple[str, list]:
    """Classify a MISSED_QUALIFYING_CANDIDATE finding against the current leader and CHECK_RESULT."""
    check, leader, spec = ctx["check"], ctx["leader"], ctx["spec"]
    cands = {c["candidate_id"]: c for c in check.get("candidates") or []}
    hard = [r["id"] for r in spec.get("requirements") or [] if str(r.get("class") or r.get("type") or "").upper() == "HARD"]
    if leader is None:
        return MATERIAL, ["no unique preferred candidate after the critic: the finding affects the recommendation"]
    cid = f.get("candidate_id")
    if cid is None:
        return INSUFFICIENT, [f.get("match_problem") or "the missed candidate is not in the applied CHECK_RESULT"]
    if cid == leader:
        if ctx["clean_pass_on_leader"] and ctx["pass_no"] > f["critic_pass"]:
            return RESOLVED, [f"{cid} is now the leader and survived critic pass {ctx['pass_no']}"]
        return MATERIAL, [f"the missed candidate {cid} is now the preferred candidate: it needs its own critic pass"]
    lc = cands.get(leader) or {}
    if lc.get("lane") != "SPECIFY NOW" or any((lc.get("cells", {}).get(r) or {}).get("status") != "PASS" for r in hard):
        return MATERIAL, [f"the leader {leader} is not SPECIFY NOW with every HARD requirement PASS"]
    mc = cands.get(cid)
    if mc is None:
        return INSUFFICIENT, [f"{cid} is not in CHECK_RESULT_v{check.get('version')}"]
    statuses = {r: (mc.get("cells", {}).get(r) or {}).get("status", "UNKNOWN") for r in hard}
    clash = sorted(r for r, st in statuses.items() if st in ("FAIL", "CONFLICT"))
    if clash:
        return MATERIAL, [f"HARD {', '.join(clash)} of {cid} is {'/'.join(statuses[r] for r in clash)} in the RUN but PASS for "
                          "the critic: a HARD compliance disagreement"]
    open_ = sorted(r for r, st in statuses.items() if st != "PASS")
    if open_ or mc.get("lane") != "SPECIFY NOW":
        return INSUFFICIENT, [f"{cid} is {mc.get('lane')} with {', '.join(open_) or 'no'} HARD requirement(s) open: "
                              "it is not shown to pass"]
    weak = [r for r in hard if (f.get("job2_rows") or {}).get(r, {}).get("status") != "PASS"
            or not any("MANUFACTURER" in a.upper() for a in (f.get("job2_rows") or {}).get(r, {}).get("authorities", []))]
    if weak:
        return INSUFFICIENT, [f"the critic's HARD PASS for {', '.join(weak)} does not rest on a manufacturer document "
                              "(weak evidence)"]
    crits, problems = ctx["ranking"]
    if problems:
        return INSUFFICIENT, problems
    if not crits:
        return MATERIAL, ["the SPEC has no approved SOFT ranking, so a second qualifying candidate cannot be shown dominated"]
    verdict, reasons = compare(leader, cid, crits, ctx["soft_values"])
    if verdict == "DOMINATED":
        return NON_MATERIAL, [f"{cid} passes every HARD requirement on manufacturer evidence and is dominated by "
                              f"{leader} on the approved ranking"] + reasons
    if verdict == "BETTER":
        return MATERIAL, [f"{cid} outranks {leader} on the approved ranking"] + reasons
    if verdict == "TIE":
        return MATERIAL, [f"{cid} ties {leader} on every approved criterion: no unique preferred candidate"] + reasons
    return INSUFFICIENT, reasons


def other_candidate_concern(f: dict, ctx: dict) -> tuple[str, list]:
    """A concern about a candidate other than the leader matters only if that candidate could outrank the leader."""
    check, leader, cid = ctx["check"], ctx["leader"], f["candidate_id"]
    hard = [r["id"] for r in ctx["spec"].get("requirements") or [] if str(r.get("class") or r.get("type") or "").upper() == "HARD"]
    lc = {c["candidate_id"]: c for c in check.get("candidates") or []}.get(leader) or {}
    if lc.get("lane") != "SPECIFY NOW" or any((lc.get("cells", {}).get(r) or {}).get("status") != "PASS" for r in hard):
        return MATERIAL, [f"the leader {leader} is not SPECIFY NOW with every HARD requirement PASS"]
    crits, problems = ctx["ranking"]
    if problems:
        return INSUFFICIENT, problems
    if not crits:
        return MATERIAL, [f"no approved SOFT ranking shows that {cid} cannot outrank {leader}"]
    verdict, reasons = compare(leader, cid, crits, ctx["soft_values"])
    if verdict == "DOMINATED":
        return NON_MATERIAL, [f"the {f.get('concern_type')} concern is about {cid}, which is dominated by {leader} on the "
                              "approved ranking whatever its own status: it cannot change the recommendation"] + reasons
    if verdict in ("BETTER", "TIE"):
        return MATERIAL, [f"the concern is about {cid}, which could outrank or tie {leader}"] + reasons
    return INSUFFICIENT, reasons


def assess(f: dict, ctx: dict) -> tuple[str, str, list]:
    """(class, status, reasons). class is MATERIAL, NON_MATERIAL or INSUFFICIENT_EVIDENCE; status adds RESOLVED."""
    if f["kind"] == MISSED:
        cls, reasons = assess_missed(f, ctx)
        if cls == RESOLVED:
            return MATERIAL, RESOLVED, reasons
        return cls, cls, reasons
    if f["kind"] == CONCERN and f.get("concern_type") not in ("SAFETY", "RELIABILITY") \
            and f.get("candidate_id") and f["candidate_id"] != ctx["leader"] and ctx["leader"]:
        cls, reasons = other_candidate_concern(f, ctx)
        return cls, cls, reasons
    # never downgraded: HARD, safety, interpretation, provenance, reliability, manufacturer-claim concerns on the leader
    why = {HARD_CHANGE: "a HARD status change on the leader (missed HARD failure / incorrect HARD PASS)",
           HARD_STATE: "a HARD state changed (C1/C2)", SAFETY: "a finding on a safety-critical requirement",
           INTERPRETATION: "a requirement interpretation finding", CONCERN: f"a {f.get('concern_type')} concern"}[f["kind"]]
    if ctx["clean_pass_on_leader"] and ctx["pass_no"] > f["critic_pass"]:
        return MATERIAL, RESOLVED, [f"{why}; settled: the RUN applied it and the current leader {ctx['leader']} "
                                    f"survived critic pass {ctx['pass_no']}"]
    return MATERIAL, MATERIAL, [f"{why}: never NON_MATERIAL; the RUN must address it and a later critic pass must clear the leader"]
