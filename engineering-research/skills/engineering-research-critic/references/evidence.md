# REFERENCE: EVIDENCE

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: none.

---

Contents:
- 4 - EXTRACT
  - Evidence grades
  - EXPLICIT APPLICABILITY
  - HUMAN-SUPPLIED EVIDENCE
- MANUFACTURER DOCUMENT SET
  - DOCUMENT STATES
  - CERTIFICATION EVIDENCE AUTHORITY
  - AUTHORITATIVE-CONFLICT RULE
- TRACEABLE CROSSWALKS
- DERIVED-EVIDENCE RULE

---

# 4 - EXTRACT

Create EVIDENCE_TABLE from the advanced candidates in DISCOVERY_PACKET.

Re-open/read the authoritative sources needed for verification. A discovery
engine's summary is not a substitute for EVIDENCE_TABLE extraction.

For each HARD requirement,
record:
- candidate
- exact MPN/configuration if known
- requirement ID
- extracted value
- unit
- operating/reference condition
- exact configuration vs family scope
- evidence grade
- source type
- source URL
- document title
- document date/revision when available
- page/table/section/configurator locator
- short supporting text/value
- retrieval date
- notes

For HARD rows, preserve the manufacturer-first authority rules below.
SOFT commercial fields are collected later in SOFT ENRICH unless the same source
is already open and the value can be captured without displacing HARD evidence.

"Not found" is valid.

EXTRACT never decides PASS/FAIL.

Do not substitute similar MPN data.

Do not silently infer that:
- family specification applies to an exact configuration
- operating range equals performance/accuracy range
- BFSL/reference accuracy equals Total Error Band
- nearby range/configuration equals the requested one

## Evidence grades

A
Manufacturer evidence for exact configuration.
For a certification/approval predicate only, also a CERTIFIER-PRIMARY record
under CERTIFICATION EVIDENCE AUTHORITY.

B
Manufacturer family evidence explicitly applicable to the configuration.

C
Distributor or reputable third-party evidence.

D
Derived/inferred evidence.

Record each row's authority with exactly one token: MANUFACTURER | CERTIFIER |
DISTRIBUTOR | THIRD_PARTY | DERIVED, and its scope EXACT or FAMILY. Authority
follows the publisher/host (CERTIFICATION EVIDENCE AUTHORITY, SECONDARY). The
grade must agree: A = MANUFACTURER + EXACT, or CERTIFIER for a
certification/approval predicate only; B = MANUFACTURER + FAMILY; C =
DISTRIBUTOR or THIRD_PARTY; D = DERIVED. HUMAN-SUPPLIED is an acquisition
channel, never an authority: a supplied record takes its original issuer's
authority under HUMAN-SUPPLIED EVIDENCE.

## EXPLICIT APPLICABILITY

Evidence supports a candidate/configuration only when it is explicitly
applicable to it (Grade B and every other "applicable" in this skill). A source
is explicitly applicable only when the source itself, or an authoritative scope
definition it directly links, establishes coverage without unsupported
inference. Accepted paths:

EXACT MODEL
- the source names the exact MPN, order code or configuration

EXPLICIT SERIES/FAMILY SCOPE
- the source explicitly defines the series/family scope
- the candidate is explicitly shown to belong to that scope
- no option, suffix, variant or qualifier relevant to the predicate excludes
  the candidate

EXPLICIT MODEL PATTERN
- the source gives a model pattern or wildcard
- every wildcard position, suffix and option code is defined in the same
  authoritative source or an authoritative scope definition it directly links
- the candidate maps to the pattern unambiguously
- every qualifier attached to the pattern is available and checked

None of these establishes applicability on its own:
- similar part-number shape or a shared prefix
- the same wattage, size, or a family name on a distributor page
- apparent wildcard matching when the wildcard meanings are undefined
- adjacent, sibling or visually similar models
- engineering expectation

UNRESOLVED QUALIFIER
- a model entry, pattern, listing or certificate carries a footnote,
  superscript, suffix condition, parenthetical marker or other qualifier whose
  meaning was not retrieved/read
- do not assume the qualifier is harmless; do not assume it excludes the
  candidate; do not invent its meaning
- applicability is unresolved; if it is needed for a HARD PASS, the requirement
  is UNKNOWN

WRONG MODEL
- an authoritative document for a different model/configuration is not
  applicable evidence for the candidate and cannot support its PASS
- on its own it is not a FAIL; FAIL needs an authoritative, applicable source
  showing that the candidate does not satisfy the frozen predicate

PASS needs adequate authority and adequate applicability. Strong authority does
not repair unresolved applicability; exact applicability does not repair
inadequate authority.

For a configuration-dependent HARD requirement, applicability must reach the
configuration being evaluated, not only the family, unless the series/family
source states that the predicate applies uniformly to that configuration. A
clearly scoped series/family source is enough; an exact-MPN document is not
required. Options not verified at level 3 stay under the EXACT CONFIGURATION
RULE.

## HUMAN-SUPPLIED EVIDENCE

In `human-supplied-evidence.md` (load: `../SKILL.md`, REFERENCE LOADING).

---

# MANUFACTURER DOCUMENT SET

Why: a prior run passed a datasheet temperature rating while a current
installation manual imposed a stricter limit.

For HARD requirements affected by installation or operating conditions,
inspect the applicable subset of:
1. exact product page or current datasheet
2. current installation/operating/user manual, if an applicable manual is
   identifiable
3. current certification/declaration record when certification is HARD

Relevant requirement types include:
- operating temperature
- derating
- electrical limits
- environmental limits
- orientation/clearances/mounting
- pressure/flow limits
- compatibility
- certification/approval
- safety limits
- other conditions that can invalidate a rating

Record document types checked.

The VERIFICATION-SOURCE BUDGET limit on primary manufacturer documents per
advanced candidate governs the normal verification pass. When that limit blocks
retrieval of an identified applicable document/record, record it as
EXISTS_NOT_RETRIEVED; if it could determine a HARD predicate, the requirement is
UNKNOWN. Recovery, if any, is only through an existing later stage under its
own rules, approvals and budgets (TARGETED ESCALATION, VERIFY ACTION, approved
research at G2, HUMAN-SUPPLIED EVIDENCE); it does not widen the normal-pass
limit.

## DOCUMENT STATES

Record the state of each applicable manufacturer document/record with exactly
one of these tokens. Document states are not requirement statuses.

RETRIEVED
- the applicable document/record was retrieved and inspected
- evaluate its evidence under the existing rules

NOT_IDENTIFIED
- after the bounded manufacturer document check, no separate applicable
  document/record could be identified
- this does not assert that the document does not exist
- record it as a completeness caveat; do not automatically erase an otherwise
  explicit, applicable exact-manufacturer PASS from checked evidence

EXISTS_NOT_RETRIEVED
- affirmative evidence shows that an applicable document/record exists (for
  example a manufacturer listing, title, document ID, download link or registry
  entry), but it was not retrieved/read
- record why with exactly one reason token: BUDGET_LIMIT (a limit blocked the
  open), or a retrieval reason: DEAD_LOCATOR | FETCH_FAILED | PAGE_MOVED |
  NOT_AT_EXPECTED_PATH | LOCATOR_NOT_RESOLVED (the RETRIEVAL FALLBACK reasons)
- affected HARD requirement = UNKNOWN if the unretrieved document could
  determine whether the predicate is satisfied
- otherwise record the caveat without changing an otherwise supported status

ACCESS_GATED
- an applicable document/record is identified but cannot be inspected because
  access requires authentication, login, account access or another access
  boundary not available in the run
- status impact is the same as EXISTS_NOT_RETRIEVED
- knowing that the record exists is not evidence that its contents satisfy the
  predicate

Do not record DOCUMENT NOT FOUND or DNF as a document state. Prose may explain a
retrieval failure, but the recorded state is one of the four tokens above.

An unavailable document is assumed neither favorable nor contradictory.

Never assume a missing document contains no restriction.

If fetching an identified public document fails in the normal verification
pass (an error, an access-denied page or a non-document is returned), the run
may retry the same locator once with a different available retrieval tool. Both
attempts count as executed opens under the BUDGET CONTRACT; the document counts
once against the primary-manufacturer-document limit. The retry is not a search
and does not look for other copies (that is RETRIEVAL FALLBACK, after an
approved VERIFY ACTION). A returned non-document (for example an HTML error page
saved under a document name) is never RETRIEVED. If the retry fails, record
EXISTS_NOT_RETRIEVED with reason FETCH_FAILED; the human may supply the record
under HUMAN-SUPPLIED EVIDENCE.

## CERTIFICATION EVIDENCE AUTHORITY

In `certification.md` (load: `../SKILL.md`, REFERENCE LOADING).

## AUTHORITATIVE-CONFLICT RULE

Two current, applicable manufacturer sources materially conflict when one
satisfies a HARD predicate and the other does not.

Then:

status = CONFLICT

Do not:
- choose the favorable source
- average values
- reinterpret one source without evidence
- keep PASS because one source supports it

An explicitly superseded older revision is not a current conflict. Record the
revision used.

For a certification/approval predicate, a current, applicable CERTIFIER-PRIMARY
record is an authoritative source under this rule alongside manufacturer
sources. Neither is assumed wrong.

---

# TRACEABLE CROSSWALKS

A crosswalk is derived evidence.

Unit definitions and exact unit conversions may be treated as deterministic
definitions.

A correspondence between standards is an evidence input.

Example:
- "EN 1.4404 = AISI 316L" must not be assumed from a generic third-party table
  as an exact material identity
- if the manufacturer itself states "1.4404 (316L)", that manufacturer evidence
  can support the mapping
- otherwise preserve both sources and use CONDITIONAL when exact equivalence is
  not established

Never silently perform technical equivalence.

---

# DERIVED-EVIDENCE RULE

Derived values remain Grade D.

A derived value may support an ordinary HARD PASS only when ALL are true:
1. source inputs are valid Grade A or applicable Grade B
2. the transformation is deterministic
3. it adds no unstated physical-behavior assumption
4. formula/operation and inputs are shown
5. no authoritative source conflicts with it

May support PASS:
- exact unit conversion
- tolerance arithmetic
- percentage applied to an exact rated value
- interpolation only when manufacturer explicitly states linear behavior
- arithmetic using an explicit manufacturer equation

Does not support PASS by itself:
- assuming a graph is linear because it looks straight
- inventing an interpolation rule
- combining derating curves without manufacturer instruction
- inferring monotonic behavior without support
- estimating a graph value too coarsely to verify the predicate

Rounding:
- compare the exact converted value
- if compliance flips only because of rounding, status = CONDITIONAL
- show both numbers

Assumption-dependent value:
- if it meets the predicate only under an unstated assumption -> CONDITIONAL
- if it cannot be evaluated -> UNKNOWN
- never FAIL solely from an assumption

Safety-critical HARD requirements require Grade A unless SPEC_vN explicitly
approved another rule; derived evidence cannot independently create a
safety-critical PASS.

---

