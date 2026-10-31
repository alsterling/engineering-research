"""G1 semantic guard (O-P6-01): which draft-SPEC rows say only what the human actually said or approved.

The frozen engineering-research RUN turns the user's request into a draft SPEC at G1. It may read a
user fact such as "400 VAC" as an engineering predicate such as "rated operational voltage >= 400 VAC".
That reading can be right, but the user did not state the operator, so it must not silently become an
approved HARD requirement. The RUN output is kept as evidence; this guard decides what may pass G1.

Every requirement row is classified, mechanically, against the user's own words and the recorded
human approvals:
  USER_STATED                      every value and the operator semantics are in the user's words
  USER_APPROVED                    an earlier explicit human approval established the value/operator
                                   (an approved design handoff, or an APPROVE at an earlier G1)
  PROPOSED_ENGINEERING_CONSTRAINT  anything else: an operator, a value, a qualifier or a property the
                                   user did not state (a reasonable interpretation or a derived limit)
  UNKNOWN                          the row's value is not known (UNKNOWN / TBD / empty)
The check is conservative by design: when the words do not show it, the row is PROPOSED and the human
decides. Standard-library Python 3.10+, no network.
"""
from __future__ import annotations

import json
import re

USER_STATED, USER_APPROVED = "USER_STATED", "USER_APPROVED"
PROPOSED, UNKNOWN = "PROPOSED_ENGINEERING_CONSTRAINT", "UNKNOWN"
CLASSES = (USER_STATED, USER_APPROVED, PROPOSED, UNKNOWN)
EQ, GE, LE, GT, LT, INCLUDES, RANGE, OTHER = "=", ">=", "<=", ">", "<", "includes", "range", "other"

# row operator -> canonical operator
ROW_OPS = {"=": EQ, "==": EQ, "is": EQ, "equals": EQ, "equal": EQ, "eq": EQ, "matches": EQ, "is true": EQ,
           ">=": GE, "=>": GE, "min": GE, "minimum": GE, "at least": GE,
           "<=": LE, "=<": LE, "max": LE, "maximum": LE, "at most": LE,
           ">": GT, "<": LT,
           "includes": INCLUDES, "include": INCLUDES, "covers": INCLUDES, "contains": INCLUDES,
           "in": RANGE, "within": RANGE, "between": RANGE, "range": RANGE, "in range": RANGE}
# user phrases -> canonical operator; longest first so "no less than" wins over "less than"
_PHRASES = [
    ("not less than", GE), ("no less than", GE), ("not lower than", GE), ("no lower than", GE),
    ("not below", GE), ("or greater", GE), ("or higher", GE), ("or more", GE), ("or above", GE),
    ("and above", GE), ("at least", GE), ("minimum of", GE), ("minimum", GE), ("min.", GE), ("min", GE),
    (">=", GE),
    ("not more than", LE), ("no more than", LE), ("not greater than", LE), ("not higher than", LE),
    ("not to exceed", LE), ("not exceeding", LE), ("must not exceed", LE), ("not exceed", LE),
    ("or less", LE), ("or lower", LE), ("or below", LE), ("at most", LE), ("up to", LE),
    ("maximum of", LE), ("maximum", LE), ("max.", LE), ("max", LE), ("<=", LE),
    ("greater than", GT), ("more than", GT), ("higher than", GT), ("exceeding", GT), ("above", GT),
    ("over", GT), (">", GT),
    ("less than", LT), ("lower than", LT), ("below", LT), ("under", LT), ("<", LT),
    ("exactly", EQ), ("equal to", EQ),
]
PHRASE = re.compile("|".join(r"(?<![\w>=<])" + re.escape(p) + (r"(?![\w=])" if p[-1].isalnum() or p[-1] == "." else "")
                             for p, _ in _PHRASES))
PHRASE_OP = dict(_PHRASES)
INCLUDE_WORDS = re.compile(r"\b(?:includ\w*|cover\w*|contain\w*|span\w*)\b")
RANGE_WORDS = re.compile(r"\b(?:between|within|from)\b|\d\s*(?:-|to)\s*\d")
NEGATION = re.compile(r"\b(?:not|no|never|without|reject\w*|exclud\w*|don't|do not|instead of)\b")
UNKNOWN_VALUE = re.compile(r"\b(?:unknown|tbd|tbc|to be determined|to be confirmed|not known|not supplied|not given|not stated)\b")
# parenthetical notes the RUN adds for the gate (open questions), not part of the requirement
NOTE = re.compile(r"\((?:[^()]*\b(?:pending|basis|see|note|confirm\w*|question|q\d+)\b[^()]*)\)")
TRUE_VALUES = {"true", "yes", "required", "present", "listed", "y", "1"}
STOP = {"a", "an", "the", "of", "and", "or", "for", "to", "in", "on", "at", "with", "by", "per", "be", "is",
        "must", "shall", "as", "it", "its", "that", "this", "from", "any"}
# physical units (canonical); any other word after a number is not a unit and the number stands alone
UNITS = {"a": "a", "amp": "a", "amps": "a", "ampere": "a", "amperes": "a", "ka": "ka", "ma": "ma",
         "v": "v", "vac": "v", "vdc": "v", "vca": "v", "kv": "kv", "mv": "mv", "w": "w", "kw": "kw", "mw": "mw",
         "hp": "hp", "va": "va", "kva": "kva", "hz": "hz", "khz": "khz", "mm": "mm", "cm": "cm", "m": "m",
         "in": "in", "inch": "in", "ft": "ft", "bar": "bar", "mbar": "mbar", "pa": "pa", "kpa": "kpa",
         "mpa": "mpa", "psi": "psi", "l/min": "l/min", "lpm": "l/min", "gpm": "gpm", "c": "c", "degc": "c",
         "f": "f", "k": "k", "kg": "kg", "g": "g", "n": "n", "nm": "nm", "rpm": "rpm", "%": "%",
         "pole": "pole", "poles": "pole", "phase": "phase", "phases": "phase", "s": "s", "ms": "ms",
         "ohm": "ohm", "db": "db", "cell": "cell", "cells": "cell", "kj": "kj", "j": "j"}
QTY = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?:\s*-\s*|\s*)(l/min|%|[a-z]+)?")


def norm(text) -> str:
    t = str(text if text is not None else "").lower()
    t = t.replace("≥", ">=").replace("≤", "<=").replace("°c", "degc").replace("° c", "degc")
    t = re.sub(r"[‐-―−]", "-", t)
    t = re.sub(r"\bv\s*a\.?c\.?\b", "vac", t)
    t = re.sub(r"\bv\s*d\.?c\.?\b", "vdc", t)
    return re.sub(r"\s+", " ", t).strip()


def strip_notes(text) -> str:
    return re.sub(r"\s+", " ", NOTE.sub(" ", norm(text))).strip()


def stem(tok: str) -> str:
    if len(tok) > 5 and tok.endswith(("ing", "ion")):
        return tok[:-3]
    if len(tok) > 4 and tok.endswith("ed"):
        return tok[:-2]
    return tok[:-1] if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss") else tok


def tokens(text) -> set:
    return {stem(t) for t in re.findall(r"[a-z0-9]+(?:\.\d+)?", norm(text)) if t not in STOP}


def quantity_spans(text: str) -> list:
    """(start, end, 'number unit') for every number in already-normalized text; unit '' when none."""
    out = []
    for m in QTY.finditer(text):
        num, unit = m.group(1), (m.group(2) or "")
        if unit in UNITS:
            out.append((m.start(), m.end(), f"{float(num):g} {UNITS[unit]}"))
        else:
            out.append((m.start(), m.start() + len(num), f"{float(num):g}"))
    return out


def quantities(text) -> set:
    return {q for _, _, q in quantity_spans(norm(text))}


def _number(q: str) -> str:
    return q.split()[0]


class UserWords:
    """The user's words, with the operator evidence next to each stated quantity."""

    def __init__(self, text: str):
        self.text = norm(text)
        self.tokens = tokens(self.text)
        self.occurrences = {}   # quantity -> list of operator sets, one per occurrence
        self.numbers = set()
        spans = quantity_spans(self.text)
        for i, (start, end, q) in enumerate(spans):
            prev_end = spans[i - 1][1] if i else 0
            nxt = spans[i + 1][0] if i + 1 < len(spans) else len(self.text)
            before = self.text[prev_end:start]
            before = re.split(r"[,;:.!?\n]\s", before)[-1]
            before = " ".join(before.split()[-6:])
            after = re.split(r"[,;:.!?\n]", self.text[end:nxt])[0]
            after = " ".join(after.split()[:3])
            ops = set()
            for window, side in ((before, "before"), (after, "after")):
                for m in PHRASE.finditer(window):
                    op = PHRASE_OP[m.group(0)]
                    # "or more" / "or less" follow the number; "at least" / "up to" precede it
                    if side == "after" and not m.group(0).startswith(("or ", "and ")) and op not in (EQ,):
                        if m.group(0) not in ("minimum", "maximum", "min", "max", "min.", "max."):
                            continue
                    ops.add(op)
            negated = bool(NEGATION.search(PHRASE.sub(" ", before)))
            sentence_start = max(self.text.rfind(c, 0, start) for c in ".;\n")
            sentence_end = min([j for j in (self.text.find(c, end) for c in ".;\n") if j >= 0] or [len(self.text)])
            sentence = self.text[sentence_start + 1:sentence_end]
            if INCLUDE_WORDS.search(sentence):
                ops.add(INCLUDES)
            if RANGE_WORDS.search(before + " " + after) or re.search(rf"\d\s*(?:-|to)\s*{re.escape(_number(q))}\b", self.text[max(0, start - 12):end]):
                ops.add(RANGE)
            self.occurrences.setdefault(q, []).append({"ops": ops, "negated": negated})
            self.numbers.add(_number(q))

    def stated(self, q: str) -> bool:
        if " " not in q:
            return q in self.numbers
        return any(not o["negated"] for o in self.occurrences.get(q, []))

    def operator_stated(self, q: str, op: str) -> bool:
        occ = [o for o in self.occurrences.get(q, []) if not o["negated"]]
        if op == EQ:
            return any(not (o["ops"] - {EQ, INCLUDES}) for o in occ)
        return any(op in o["ops"] for o in occ)


def row_class(row) -> str:
    """HARD or SOFT; the RUN may write the requirement class as "class" or as "type"."""
    return str(row.get("class") or row.get("type") or "").upper()


RANKING_OP = re.compile(r"^(?:minimi[sz]e|maximi[sz]e|min|max|lower|higher|lowest|highest|prefer\w*)\b")


def row_operator(row) -> str:
    return ROW_OPS.get(norm(row.get("operator", "")), OTHER)


def row_value(row) -> str:
    return strip_notes(row.get("value", ""))


def is_unknown(row) -> bool:
    v = norm(row.get("value", ""))
    if not v and row_class(row) == "SOFT" and RANKING_OP.match(norm(row.get("operator", ""))):
        return False  # a SOFT ranking criterion states a direction, not a value: the human approves it, it is not UNKNOWN
    return not v or bool(UNKNOWN_VALUE.search(v)) or norm(row.get("operator", "")) in ("unknown", "tbd")


def row_quantities(row) -> set:
    """Every quantity the row asserts: in its parameter, value + unit, and condition (notes removed)."""
    value, unit = row_value(row), norm(row.get("unit", ""))
    main = quantities(f"{value} {unit}") if re.fullmatch(r"\d+(?:\.\d+)?", value) else quantities(value)
    return main | quantities(strip_notes(row.get("parameter", ""))) | quantities(strip_notes(row.get("condition", "")))


def main_quantity(row):
    value, unit = row_value(row), norm(row.get("unit", ""))
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        q = quantities(f"{value} {unit}")
        return next(iter(q)) if len(q) == 1 else None
    return None


def claim_tokens(row) -> set:
    """The words a non-numeric row asserts: its value, or for a yes/no row the property its parameter names."""
    value = row_value(row)
    text = strip_notes(row.get("parameter", "")) if value in TRUE_VALUES else value
    return tokens(text)


def signature(row) -> str:
    """The row's requirement semantics (operator, values, asserted words), independent of id and wording notes."""
    sig = {"op": row_operator(row) if row_operator(row) != OTHER else norm(row.get("operator", "")),
           "class": row_class(row),
           "quantities": sorted(row_quantities(row)),
           "value": row_value(row) if main_quantity(row) is None else main_quantity(row),
           "unit": "" if main_quantity(row) else norm(row.get("unit", "")),
           "unknown": is_unknown(row)}
    if main_quantity(row) is None:
        sig["words"] = sorted(claim_tokens(row))
    return json.dumps(sig, sort_keys=True)


def classify_row(row: dict, user: UserWords, approvals: list) -> dict:
    """{id, class, semantic, reason}. approvals: [{"signature", "ref"}] from explicit human approvals."""
    rid = row.get("id")
    value = row.get("value")
    out = {"id": rid, "class": row_class(row),
           "text": f"{row.get('parameter', '')} {row.get('operator', '')} {'' if value is None else value} {row.get('unit', '')}"
                   .replace("  ", " ").strip(),
           "signature": signature(row)}
    if is_unknown(row):
        return {**out, "semantic": UNKNOWN, "reason": "the value is not known; it stays UNKNOWN until the human supplies it"}
    approved = next((a for a in approvals if a["signature"] == out["signature"]), None)
    reasons = []
    origin = str(row.get("origin", "USER")).upper()
    if origin not in ("USER", ""):
        reasons.append(f"origin {row.get('origin')} (an AI proposal, not the user's words)")
    missing = sorted(q for q in row_quantities(row) if not user.stated(q))
    if missing:
        reasons.append("value(s) the user did not state: " + ", ".join(missing))
    op = row_operator(row)
    q = main_quantity(row)
    if q is not None:
        if op == OTHER:
            reasons.append(f"operator {row.get('operator')!r} is not one the user's words can show")
        elif q not in missing and not user.operator_stated(q, op):
            said = sorted({o for occ in user.occurrences.get(q, []) for o in occ["ops"]}) or ["no operator"]
            reasons.append(f"operator {op!r} on {q} is an interpretation: the user's words give {', '.join(said)}")
    else:
        value_q = quantities(row_value(row))
        for vq in sorted(value_q - set(missing)):
            if op == OTHER or not user.operator_stated(vq, op):
                said = sorted({o for occ in user.occurrences.get(vq, []) for o in occ["ops"]}) or ["no operator"]
                reasons.append(f"operator {row.get('operator')!r} on {vq} is an interpretation: the user's words give "
                               + ", ".join(said))
        if not value_q and op not in (EQ, INCLUDES):
            reasons.append(f"operator {row.get('operator')!r} on a non-numeric value is an interpretation")
        extra = sorted(t for t in claim_tokens(row) if t not in user.tokens)
        if extra:
            reasons.append("asserts words the user did not state: " + ", ".join(extra))
    if not reasons:
        return {**out, "semantic": USER_STATED, "reason": "value and operator are in the user's words"}
    if approved:
        return {**out, "semantic": USER_APPROVED, "reason": f"explicitly approved by the human ({approved['ref']})"}
    return {**out, "semantic": PROPOSED, "reason": "; ".join(reasons)}


def classify_spec(spec: dict, user_text: str, approvals: list) -> list:
    user = UserWords(user_text)
    return [classify_row(r, user, approvals) for r in spec.get("requirements") or [] if isinstance(r, dict)]


def handoff_approvals(handoff: dict | None) -> list:
    """HARD requirements of a design handoff the human approved at the design gate."""
    if not isinstance(handoff, dict) or handoff.get("status") != "APPROVED":
        return []
    out = []
    for r in handoff.get("hard_requirements") or []:
        if isinstance(r, dict):
            row = {"class": "HARD", "parameter": r.get("parameter", ""), "operator": r.get("operator", ""),
                   "value": r.get("value", ""), "unit": r.get("unit", ""), "condition": r.get("condition", "")}
            out.append({"signature": signature(row), "ref": handoff.get("approval_ref", "design gate")})
    return out


def decide(rows: list, ans: dict) -> tuple[dict, list]:
    """Check a G1 APPROVE_SPEC answer against the classified rows. Returns ({id: decision}, problems).

    decision per row: APPROVE (USER_STATED / USER_APPROVED by APPROVE_SPEC, PROPOSED only when the human
    wrote APPROVE for it), REJECT (PROPOSED only), KEEP_UNKNOWN (UNKNOWN acknowledged)."""
    given = ans.get("requirement_decisions") or {}
    ack = ans.get("acknowledged_unknowns") or []
    ack_all = ack == "ALL" or ack == ["ALL"]
    ids = {r["id"] for r in rows}
    problems = [f"{rid}: no such requirement in the draft SPEC" for rid in given if rid not in ids]
    problems += [f"{rid}: no such requirement in the draft SPEC" for rid in ([] if ack_all else ack) if rid not in ids]
    out = {}
    for r in rows:
        rid, sem, d = r["id"], r["semantic"], str(given.get(r["id"], "")).upper()
        if d and d not in ("APPROVE", "REJECT"):
            problems.append(f"{rid}: decision must be APPROVE or REJECT, not {given[rid]!r}")
            continue
        if sem == UNKNOWN:
            if d:
                problems.append(f"{rid} is UNKNOWN: it cannot be approved or rejected as a value; acknowledge it in "
                                "acknowledged_unknowns (it stays UNKNOWN), or supply the value with CHANGE_SPEC")
            elif ack_all or rid in ack:
                out[rid] = "KEEP_UNKNOWN"
            else:
                problems.append(f"{rid} is UNKNOWN: acknowledge it (it stays UNKNOWN) or supply it with CHANGE_SPEC")
        elif sem == PROPOSED:
            if not d:
                problems.append(f"{rid} is a PROPOSED_ENGINEERING_CONSTRAINT ({r['text']}): APPROVE or REJECT it explicitly")
            else:
                out[rid] = d
        else:
            if d == "REJECT":
                problems.append(f"{rid} is {sem}: rejecting what you stated or approved is a change; use CHANGE_SPEC with text")
            else:
                out[rid] = "APPROVE"
    return out, problems


def post_g1_problems(spec: dict, g1: dict) -> list:
    """After G1, every HARD row must be one the human approved at G1 with the same semantics."""
    if not g1:
        return ["no G1 semantic approval is recorded"]
    rows = {r["id"]: r for r in g1.get("rows", [])}
    problems = []
    for r in (spec or {}).get("requirements") or []:
        if not isinstance(r, dict):
            continue
        rid, hard = r.get("id"), row_class(r) == "HARD"
        g = rows.get(rid)
        if g is None:
            if hard:
                problems.append(f"HARD {rid} was not in the SPEC approved at G1: no new HARD requirement after G1")
            continue
        if g["decision"] == "REJECT" and hard:
            problems.append(f"HARD {rid} was REJECTED at G1 ({g['text']}): it cannot be a HARD requirement")
        elif signature(r) != g["signature"]:
            problems.append(f"{rid} changed after G1 ({g['text']} -> {r.get('parameter', '')} {r.get('operator', '')} "
                            f"{r.get('value', '')} {r.get('unit', '')}): a SPEC change needs a reopened G1")
    return problems
